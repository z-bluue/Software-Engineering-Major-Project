const { createApp, ref, onMounted, nextTick } = Vue;
const { Search } = ElementPlusIconsVue;

const app = createApp({
    setup() {
        const apiStatus = ref('offline');
        const datasetInfo = ref({});
        const dataLoaded = ref(false);
        const searching = ref(false);
        
        const queryForm = ref({
            cell_index: 0,
            top_k: 10,
            metric: 'l2',
            filter_field: '',
            filter_value: ''
        });

        const colorBy = ref('cell_type');
        const currentFieldValues = ref([]);
        const searchResults = ref([]);
        const currentZoom = ref(1.0);
        
        // ECharts instance and data
        let chartInstance = null;
        let coordsDataRaw = [];
        let groupedSeriesData = {}; 
        
        let colorMap = {};
        const palette = [
            '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc',
            '#ff7f50', '#87cefa', '#da70d6', '#32cd32', '#6495ed', '#ff69b4', '#ba55d3', '#cd5c5c', '#ffa500'
        ];

        const checkApiStatus = async () => {
            try {
                const res = await axios.get('http://127.0.0.1:5000/api/dataset/info');
                if (res.data && res.data.success) {
                    apiStatus.value = 'online';
                    datasetInfo.value = res.data.data;
                }
            } catch (e) {
                console.error("Backend not running or CORS blocked.", e);
            }
        };

        const fetchFieldValues = async (val) => {
            queryForm.value.filter_value = '';
            currentFieldValues.value = [];
            if (!val) return;
            try {
                const res = await axios.get(`http://127.0.0.1:5000/api/dataset/column/${val}/values`);
                if (res.data.success) {
                    currentFieldValues.value = res.data.values;
                }
            } catch (e) {
                console.error("Error fetching field values", e);
            }
        };

        const loadUMAPData = () => {
            // Load CSV using PapaParse
            Papa.parse("../成员B文件/data/cell_2d_coords.csv", {
                download: true,
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true,
                complete: function(results) {
                    coordsDataRaw = results.data;
                    processChartData();
                    renderChart();
                    dataLoaded.value = true;
                },
                error: function(err) {
                    console.error("Error parsing CSV:", err);
                    ElementPlus.ElMessage.error("UMAP坐标数据加载失败，请检查文件是否存在并通过本地服务器运行！");
                }
            });
        };

        const processChartData = () => {
            groupedSeriesData = {};
            colorMap = {};
            let cIndex = 0;
            const key = colorBy.value;
            coordsDataRaw.forEach(row => {
                if(row.cell_index == null || row.umap_1 == null) return;
                const type = String(row[key] || 'Unknown');
                if (!groupedSeriesData[type]) {
                    groupedSeriesData[type] = [];
                    colorMap[type] = palette[cIndex % palette.length];
                    cIndex++;
                }
                // Store [x, y, cell_index, cell_type, disease, AgeGroup] internally for echarts
                groupedSeriesData[type].push([row.umap_1, row.umap_2, row.cell_index, row.cell_type, row.disease, row.AgeGroup]);
            });
        };

        const changeColorBy = () => {
            if (!dataLoaded.value) return;
            chartInstance.clear(); // 清除之前的系列和图例缓存，防止产生重影
            processChartData();
            renderChart();
            if (searchResults.value.length > 0) {
                highlightResults(searchResults.value, queryForm.value.cell_index);
            }
        };

        const renderChart = () => {
            if (!chartInstance) {
                chartInstance = echarts.init(document.getElementById('umapChart'));
                window.addEventListener('resize', () => chartInstance.resize());
                
                // 监听缩放事件，动态调整散点大小（增加防抖，避免拖拽缩放时画面撕裂与不同步）
                let zoomTimeout = null;
                let lastAppliedSize = 2; // 记录上次点的大小，如果没有发生质变就绝不打断渲染，彻底解决“闪”的问题

                chartInstance.on('dataZoom', function (params) {
                    if (zoomTimeout) clearTimeout(zoomTimeout);
                    
                    zoomTimeout = setTimeout(() => {
                        const option = chartInstance.getOption();
                        
                        // 获取当前缩放级别的起始与结束百分比
                        let start = 0, end = 100;
                        if (params.batch && params.batch.length > 0) {
                            start = params.batch[0].start;
                            end = params.batch[0].end;
                        } else if (params.start !== undefined && params.end !== undefined) {
                            start = params.start;
                            end = params.end;
                        }

                        const zoomRange = end - start;
                        if (zoomRange <= 0) return;
                        
                        // 计算放大倍数
                        const zoomScale = 100 / zoomRange;
                        currentZoom.value = zoomScale.toFixed(1);
                        
                        // 【新逻辑】直接让大小随倍数线性缩放 (加入平滑系数，最小限制为2)
                        // 使用 Math.round 使其呈整数阶梯变化，过滤掉微小波动的重复渲染
                        let targetSize = Math.max(2, Math.round(zoomScale));

                        // 当尺寸由于倍数变化导致真正的整型像素变动时，才去触发重绘机制
                        if (targetSize !== lastAppliedSize) {
                            lastAppliedSize = targetSize;
                            
                            const mergeSeries = option.series.map(s => {
                                let newSize = targetSize;
                                let style = {};

                                if (s.name === 'Query Cell') {
                                    newSize = targetSize * 3;
                                    style = { color: '#ff0000' };
                                } else if (s.name === 'Search Results') {
                                    newSize = targetSize * 2;
                                    style = { color: '#ffff00', borderColor: '#000', borderWidth: 1 };
                                } else {
                                    style = { color: colorMap[s.name], opacity: 0.6 };
                                }

                                return {
                                    name: s.name,
                                    symbolSize: newSize,
                                    itemStyle: style
                                };
                            });

                            chartInstance.setOption({ series: mergeSeries });
                        }
                    }, 50); // 因为绝大部分时候不重绘，可以把延时极大压低到 50ms 获取最直接的反馈
                });
            }

            const series = [];
            
            // Base background data
            for (let type in groupedSeriesData) {
                series.push({
                    name: type,
                    type: 'scatter',
                    symbolSize: 2, // 默认初始时给2，全局图比较精致
                    large: true,     // Optimize for thousands of points
                    largeThreshold: 2000,
                    itemStyle: { color: colorMap[type], opacity: 0.6 },
                    data: groupedSeriesData[type],
                    zlevel: 0
                });
            }

            const option = {
                title: {
                    text: '细胞 UMAP 分布图',
                    left: 'center',
                    top: 10
                },
                tooltip: {
                    trigger: 'item',
                    formatter: function(params) {
                        if (params.seriesName === 'Query Cell' || params.seriesName === 'Search Results') {
                            return `<b>${params.seriesName}</b><br/>
                                    Index: ${params.value[2]}<br/>
                                    Type: ${params.value[3]}`;
                        }
                        return `Index: ${params.value[2]}<br/>
                                Type: ${params.value[3]}<br/>
                                Disease: ${params.value[4]}<br/>
                                AgeGroup: ${params.value[5]}`;
                    }
                },
                legend: {
                    type: 'scroll',
                    orient: 'vertical',
                    right: 10,
                    top: 50,
                    bottom: 20
                },
                grid: {
                    left: '5%',
                    right: '5%',
                    bottom: '5%',
                    top: '10%',
                    containLabel: true
                },
                toolbox: {
                    feature: {
                        restore: { title: '还原全局视图' },
                        saveAsImage: { title: '保存为图片' }
                    }
                },
                dataZoom: [
                    { type: 'inside', xAxisIndex: 0 },
                    { type: 'inside', yAxisIndex: 0 }
                ],
                xAxis: {
                    type: 'value',
                    name: 'UMAP 1',
                    scale: true,
                    axisLabel: { show: false },
                    axisTick: { show: false },
                    splitLine: { show: false }
                },
                yAxis: {
                    type: 'value',
                    name: 'UMAP 2',
                    scale: true,
                    axisLabel: { show: false },
                    axisTick: { show: false },
                    splitLine: { show: false }
                },
                color: [
                    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc',
                    '#ff7f50', '#87cefa', '#da70d6', '#32cd32', '#6495ed', '#ff69b4', '#ba55d3', '#cd5c5c', '#ffa500'
                ],
                series: series
            };

            chartInstance.setOption(option, true);
        };

        const highlightResults = (results, queryIndex) => {
            if (!chartInstance) return;
            const option = chartInstance.getOption();
            
            // 计算当前缩放倍率，保证检索高亮时不破坏已有的动态图点大小
            let baseSize = 2; // 默认全局最适基础大小为2
            if (option.dataZoom && option.dataZoom.length > 0) {
                const start = option.dataZoom[0].start || 0;
                const end = option.dataZoom[0].end || 100;
                const zoomRange = end - start;
                if (zoomRange > 0) {
                    const zoomScale = 100 / zoomRange;
                    baseSize = Math.max(2, Math.round(zoomScale * 1.2));
                }
            }
            
            // 完全重新构建基础点阵系，防止 ECharts getOption() 在大点量下因为优化而丢失部分分类数据
            const series = [];
            for (let type in groupedSeriesData) {
                series.push({
                    name: type,
                    type: 'scatter',
                    symbolSize: baseSize,
                    large: true,     // 保证万级数据依然可以流畅渲染
                    largeThreshold: 2000,
                    itemStyle: { color: colorMap[type], opacity: 0.6 },
                    data: groupedSeriesData[type],
                    zlevel: 0
                });
            }

            // Find query coordinates
            const queryRow = coordsDataRaw.find(row => row.cell_index === queryIndex);
            
            if (queryRow) {
                series.push({
                    name: 'Query Cell',
                    type: 'effectScatter',
                    symbolSize: baseSize * 3,
                    itemStyle: { color: '#ff0000' },
                    data: [[queryRow.umap_1, queryRow.umap_2, queryRow.cell_index, queryRow.cell_type]],
                    zlevel: 5
                });
            }

            // Find result coordinates
            const resultData = [];
            results.forEach(res => {
                const rRow = coordsDataRaw.find(row => row.cell_index === res.cell_index);
                if (rRow) {
                    resultData.push([rRow.umap_1, rRow.umap_2, rRow.cell_index, rRow.cell_type]);
                }
            });

            if (resultData.length > 0) {
                series.push({
                    name: 'Search Results',
                    type: 'scatter',
                    symbolSize: baseSize * 2,
                    itemStyle: { color: '#ffff00', borderColor: '#000', borderWidth: 1 },
                    data: resultData,
                    zlevel: 4
                });
            }

            // 使用 replaceMerge 更新 series，这样既不丢失数据，又能完美保留用户当前的放大和拖拽状态
            chartInstance.setOption({
                series: series
            }, { replaceMerge: ['series'] });
        };

        const doSearch = async () => {
            if (apiStatus.value !== 'online') {
                ElementPlus.ElMessage.warning('后端不可用，请启动 Flask 服务！');
                return;
            }

            searching.value = true;
            try {
                const payload = {
                    cell_index: queryForm.value.cell_index,
                    top_k: queryForm.value.top_k,
                    metric: queryForm.value.metric
                };
                if (queryForm.value.filter_field && queryForm.value.filter_value) {
                    payload.filter_field = queryForm.value.filter_field;
                    payload.filter_value = queryForm.value.filter_value;
                }

                const res = await axios.post('http://127.0.0.1:5000/api/search', payload);
                if (res.data.success) {
                    searchResults.value = res.data.results;
                    ElementPlus.ElMessage.success(`检索成功！找到 ${searchResults.value.length} 个结果`);
                    highlightResults(res.data.results, queryForm.value.cell_index);
                } else {
                    ElementPlus.ElMessage.error(`检索失败: ${res.data.message}`);
                }
            } catch (e) {
                ElementPlus.ElMessage.error(`请求异常: ${e.message}`);
                console.error(e);
            } finally {
                searching.value = false;
            }
        };

        onMounted(() => {
            checkApiStatus();
            nextTick(() => {
                loadUMAPData();
            });
        });

        return {
            apiStatus,
            datasetInfo,
            dataLoaded,
            searching,
            queryForm,
            colorBy,
            changeColorBy,
            currentFieldValues,
            fetchFieldValues,
            searchResults,
            currentZoom,
            doSearch
        };
    }
});

// Register Icons
app.component('Search', Search);

app.use(ElementPlus);
app.mount('#app');