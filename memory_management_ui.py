import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from memory_management import MemoryManager, InstructionGenerator
from typing import List, Dict

def create_memory_visualization(memory_states: List[List[int]], page_accesses: List[int], memory_size: int):
    """创建内存状态可视化"""
    fig = go.Figure()
    
    # 创建时间轴
    time_steps = list(range(len(memory_states)))
    
    # 为每个内存槽位创建trace
    for slot in range(memory_size):
        slot_values = []
        for state in memory_states:
            if slot < len(state):
                slot_values.append(state[slot])
            else:
                slot_values.append(None)
        
        fig.add_trace(go.Scatter(
            x=time_steps,
            y=[slot] * len(time_steps),
            mode='markers+text',
            text=[str(val) if val is not None else '' for val in slot_values],
            textposition='middle center',
            marker=dict(
                size=30,
                color=[val if val is not None else -1 for val in slot_values],
                colorscale='viridis',
                showscale=True,
                colorbar=dict(title="页面号")
            ),
            name=f'内存槽位 {slot}',
            hovertemplate='<b>时间步: %{x}</b><br>内存槽位: %{y}<br>页面号: %{text}<extra></extra>'
        ))
    
    fig.update_layout(
        title='内存状态变化可视化',
        xaxis_title='访问步骤',
        yaxis_title='内存槽位',
        height=400,
        yaxis=dict(range=[-0.5, memory_size-0.5])
    )
    
    return fig

def create_hit_rate_comparison(comparison_data: Dict):
    """创建命中率比较图"""
    memory_sizes = list(comparison_data.keys())
    algorithms = list(comparison_data[memory_sizes[0]].keys())
    
    fig = go.Figure()
    
    for algorithm in algorithms:
        hit_rates = [comparison_data[size][algorithm]['hit_rate'] for size in memory_sizes]
        fig.add_trace(go.Scatter(
            x=memory_sizes,
            y=hit_rates,
            mode='lines+markers',
            name=algorithm,
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title='不同内存容量下的命中率比较',
        xaxis_title='内存容量（页数）',
        yaxis_title='命中率',
        yaxis=dict(range=[0, 1]),
        height=400,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def create_page_fault_comparison(comparison_data: Dict):
    """创建缺页次数比较图"""
    memory_sizes = list(comparison_data.keys())
    algorithms = list(comparison_data[memory_sizes[0]].keys())
    
    fig = go.Figure()
    
    for algorithm in algorithms:
        page_faults = [comparison_data[size][algorithm]['page_faults'] for size in memory_sizes]
        fig.add_trace(go.Scatter(
            x=memory_sizes,
            y=page_faults,
            mode='lines+markers',
            name=algorithm,
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title='不同内存容量下的缺页次数比较',
        xaxis_title='内存容量（页数）',
        yaxis_title='缺页次数',
        height=400,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )
    
    return fig

def main():
    st.set_page_config(
        page_title="虚拟内存管理模拟器", 
        page_icon="💾", 
        layout="wide"
    )
    
    st.title("💾 虚拟内存管理模拟器")
    st.markdown("---")
    
    # 初始化会话状态
    if 'memory_manager' not in st.session_state:
        st.session_state.memory_manager = MemoryManager()
    if 'instructions' not in st.session_state:
        st.session_state.instructions = None
    if 'simulation_result' not in st.session_state:
        st.session_state.simulation_result = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'is_simulating' not in st.session_state:
        st.session_state.is_simulating = False
    
    # 侧边栏控制面板
    with st.sidebar:
        st.header("🎛️ 控制面板")
        
        # 实验配置
        st.subheader("实验配置")
        
        # 算法选择
        algorithm = st.selectbox(
            "选择页面置换算法",
            options=['FIFO', 'LRU', 'OPT', 'LFR'],
            index=0,
            help="FIFO: 先进先出\nLRU: 最近最少使用\nOPT: 最佳淘汰算法\nLFR: 最少访问页面算法"
        )
        
        # 内存容量选择
        memory_size = st.slider(
            "内存容量（页数）",
            min_value=4,
            max_value=32,
            value=8,
            step=2,
            help="可选择4到32页的内存容量"
        )
        
        # 指令序列控制
        st.subheader("指令序列")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 生成新序列", use_container_width=True):
                generator = InstructionGenerator()
                st.session_state.instructions = generator.generate_instructions()
                st.session_state.simulation_result = None
                st.session_state.current_step = 0
                st.session_state.is_simulating = False
                st.success("新指令序列已生成！")
        
        with col2:
            if st.button("📊 开始模拟", use_container_width=True):
                if st.session_state.instructions is not None:
                    result = st.session_state.memory_manager.simulate(
                        algorithm, memory_size, st.session_state.instructions
                    )
                    st.session_state.simulation_result = result
                    st.session_state.current_step = 0
                    st.session_state.is_simulating = True
                    st.success("模拟开始！")
                else:
                    st.error("请先生成指令序列！")
        
        # 步进控制
        if st.session_state.simulation_result:
            st.subheader("步进控制")
            
            max_steps = len(st.session_state.simulation_result['access_log'])
            
            # 步骤滑块
            step = st.slider(
                "当前步骤",
                min_value=0,
                max_value=max_steps,
                value=st.session_state.current_step,
                help=f"总共{max_steps}个访问步骤"
            )
            st.session_state.current_step = step
            
            # 步进按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("⏮️", help="重置到开始"):
                    st.session_state.current_step = 0
                    st.rerun()
            
            with col2:
                if st.button("▶️", help="下一步"):
                    if st.session_state.current_step < max_steps:
                        st.session_state.current_step += 1
                        st.rerun()
            
            with col3:
                if st.button("⏭️", help="跳到最后"):
                    st.session_state.current_step = max_steps
                    st.rerun()
            
            # 自动播放
            auto_play = st.checkbox("🔄 自动播放")
            if auto_play and st.session_state.current_step < max_steps:
                time.sleep(0.5)
                st.session_state.current_step += 1
                st.rerun()
        
        # 批量比较
        st.subheader("性能比较")
        if st.button("📈 比较所有算法", use_container_width=True):
            if st.session_state.instructions is not None:
                with st.spinner("正在比较算法性能..."):
                    memory_sizes = list(range(4, 33, 4))  # 4, 8, 12, 16, 20, 24, 28, 32
                    comparison = st.session_state.memory_manager.compare_algorithms(
                        memory_sizes, st.session_state.instructions
                    )
                    st.session_state.comparison_result = comparison
                st.success("比较完成！")
            else:
                st.error("请先生成指令序列！")
    
    # 主显示区域
    tab1, tab2, tab3, tab4 = st.tabs(["📋 实时模拟", "📊 性能分析", "🔍 详细日志", "📈 批量比较"])
    
    with tab1:
        st.subheader("实时模拟")
        
        if st.session_state.simulation_result and st.session_state.current_step > 0:
            result = st.session_state.simulation_result
            current_step = st.session_state.current_step
            
            # 当前状态信息
            col1, col2, col3, col4 = st.columns(4)
            
            # 截取到当前步骤的日志
            current_log = result['access_log'][:current_step]
            current_faults = sum(1 for log in current_log if log['is_fault'])
            current_hit_rate = 1 - (current_faults / current_step) if current_step > 0 else 0
            
            with col1:
                st.metric("当前步骤", f"{current_step}/{len(result['access_log'])}")
            with col2:
                st.metric("累计缺页次数", current_faults)
            with col3:
                st.metric("当前命中率", f"{current_hit_rate:.3f}")
            with col4:
                if current_step > 0:
                    current_page = result['access_log'][current_step-1]['page']
                    st.metric("当前访问页面", current_page)
            
            # 内存状态可视化
            st.subheader("内存状态可视化")
            
            if current_step > 0:
                # 获取内存状态序列
                memory_states = []
                for i in range(current_step):
                    memory_states.append(result['access_log'][i]['memory_after'])
                
                # 创建内存可视化
                if memory_states:
                    # 显示当前内存状态
                    current_memory = result['access_log'][current_step-1]['memory_after']
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # 内存槽位可视化
                        memory_df = pd.DataFrame({
                            '内存槽位': range(memory_size),
                            '页面号': [current_memory[i] if i < len(current_memory) else None 
                                     for i in range(memory_size)],
                            '状态': ['占用' if i < len(current_memory) else '空闲' 
                                   for i in range(memory_size)]
                        })
                        
                        fig = px.bar(
                            memory_df, 
                            x='内存槽位', 
                            y=[1] * memory_size,
                            color='页面号',
                            text='页面号',
                            title='当前内存状态',
                            color_continuous_scale='viridis'
                        )
                        fig.update_traces(textposition='inside')
                        fig.update_layout(height=300, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.write("**内存详情**")
                        for i, page in enumerate(current_memory):
                            st.write(f"槽位 {i}: 页面 {page}")
                        
                        for i in range(len(current_memory), memory_size):
                            st.write(f"槽位 {i}: 空闲")
            
            # 最近访问历史
            if current_step > 0:
                st.subheader("最近访问历史")
                recent_steps = max(0, current_step - 10)
                recent_log = result['access_log'][recent_steps:current_step]
                
                log_df = pd.DataFrame([
                    {
                        '步骤': recent_steps + i + 1,
                        '访问页面': log['page'],
                        '结果': log['action'],
                        '是否缺页': '✅' if log['is_fault'] else '❌'
                    }
                    for i, log in enumerate(recent_log)
                ])
                
                st.dataframe(log_df, use_container_width=True, hide_index=True)
        
        else:
            st.info("请先生成指令序列并开始模拟")
    
    with tab2:
        st.subheader("性能分析")
        
        if st.session_state.simulation_result:
            result = st.session_state.simulation_result
            
            # 性能指标
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("算法", result['algorithm'])
            with col2:
                st.metric("内存容量", f"{result['memory_size']} 页")
            with col3:
                st.metric("总访问次数", result['total_accesses'])
            with col4:
                st.metric("缺页次数", result['page_faults'])
            
            # 命中率和缺页率
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("命中率", f"{result['hit_rate']:.3f}")
            with col2:
                st.metric("缺页率", f"{1-result['hit_rate']:.3f}")
            
            # 页面访问分布
            st.subheader("页面访问分布")
            page_counts = pd.Series(result['pages']).value_counts().sort_index()
            
            fig = px.bar(
                x=page_counts.index,
                y=page_counts.values,
                labels={'x': '页面号', 'y': '访问次数'},
                title='各页面访问频次分布'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 缺页分布
            st.subheader("缺页时间分布")
            fault_steps = [i for i, log in enumerate(result['access_log']) if log['is_fault']]
            
            if fault_steps:
                fig = px.scatter(
                    x=fault_steps,
                    y=[1] * len(fault_steps),
                    labels={'x': '访问步骤', 'y': ''},
                    title='缺页发生时间点'
                )
                fig.update_layout(yaxis=dict(showticklabels=False))
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("请先运行模拟以查看性能分析")
    
    with tab3:
        st.subheader("详细访问日志")
        
        if st.session_state.simulation_result:
            result = st.session_state.simulation_result
            
            # 创建详细日志表
            log_data = []
            for i, log in enumerate(result['access_log']):
                log_data.append({
                    '步骤': i + 1,
                    '访问页面': log['page'],
                    '操作结果': log['action'],
                    '是否缺页': '是' if log['is_fault'] else '否',
                    '访问前内存': str(log['memory_before']),
                    '访问后内存': str(log['memory_after'])
                })
            
            log_df = pd.DataFrame(log_data)
            
            # 添加筛选选项
            col1, col2 = st.columns(2)
            with col1:
                show_only_faults = st.checkbox("只显示缺页")
            with col2:
                page_filter = st.selectbox(
                    "筛选页面",
                    options=['全部'] + sorted(list(set(result['pages']))),
                    index=0
                )
            
            # 应用筛选
            filtered_df = log_df.copy()
            if show_only_faults:
                filtered_df = filtered_df[filtered_df['是否缺页'] == '是']
            if page_filter != '全部':
                filtered_df = filtered_df[filtered_df['访问页面'] == page_filter]
            
            st.dataframe(filtered_df, use_container_width=True, height=400)
            
            # 导出功能
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 下载日志CSV",
                data=csv,
                file_name=f"memory_log_{algorithm}_{memory_size}pages.csv",
                mime="text/csv"
            )
        
        else:
            st.info("请先运行模拟以查看详细日志")
    
    with tab4:
        st.subheader("算法性能批量比较")
        
        if 'comparison_result' in st.session_state:
            comparison = st.session_state.comparison_result['comparison']
            
            # 命中率比较图
            fig1 = create_hit_rate_comparison(comparison)
            st.plotly_chart(fig1, use_container_width=True)
            
            # 缺页次数比较图
            fig2 = create_page_fault_comparison(comparison)
            st.plotly_chart(fig2, use_container_width=True)
            
            # 详细比较表
            st.subheader("详细性能数据")
            
            # 准备表格数据
            table_data = []
            memory_sizes = sorted(comparison.keys())
            algorithms = list(comparison[memory_sizes[0]].keys())
            
            for size in memory_sizes:
                for alg in algorithms:
                    data = comparison[size][alg]
                    table_data.append({
                        '内存容量': size,
                        '算法': alg,
                        '缺页次数': data['page_faults'],
                        '命中率': data['hit_rate'],
                        '缺页率': 1-data['hit_rate']
                    })
            
            comparison_df = pd.DataFrame(table_data)
            
            # 透视表显示
            pivot_table = comparison_df.pivot(index='内存容量', columns='算法', values='命中率')
            st.write("**命中率对比表**")
            # 手动格式化显示，避免样式问题
            formatted_pivot = pivot_table.round(3)
            st.dataframe(formatted_pivot, use_container_width=True)
            
            # 最佳性能统计
            st.subheader("最佳性能统计")
            
            best_performers = {}
            for size in memory_sizes:
                best_hit_rate = max(comparison[size][alg]['hit_rate'] for alg in algorithms)
                best_algs = [alg for alg in algorithms 
                           if comparison[size][alg]['hit_rate'] == best_hit_rate]
                best_performers[size] = best_algs
            
            for size, algs in best_performers.items():
                st.write(f"**{size}页内存**: {', '.join(algs)} (命中率: {comparison[size][algs[0]]['hit_rate']:.3f})")
        
        else:
            st.info("请点击左侧的'比较所有算法'按钮开始批量比较")
    
    # 底部说明
    st.markdown("---")
    st.markdown("""
    ### 📖 使用说明
    
    #### 🔧 实验配置
    - **算法选择**: 四种页面置换算法可选
      - **FIFO**: 先进先出，淘汰最早进入内存的页面
      - **LRU**: 最近最少使用，淘汰最长时间未被访问的页面  
      - **OPT**: 最佳淘汰算法，淘汰将来最长时间不会被访问的页面
      - **LFR**: 最少访问页面算法，淘汰访问次数最少的页面
    - **内存容量**: 可选择4-32页的内存容量
    
    #### 📊 模拟功能
    - **实时模拟**: 逐步观察页面置换过程
    - **内存可视化**: 直观显示内存状态变化
    - **性能分析**: 命中率、缺页率等关键指标
    - **批量比较**: 对比不同算法在各种内存容量下的性能
    
    #### 💡 实验原理
    - 指令序列按实验要求生成：50%顺序执行，25%低地址分布，25%高地址分布
    - 虚存容量32K，每页1K，共32页，每页存放10条指令
    - 320条指令对应320次页面访问
    """)

if __name__ == "__main__":
    main() 