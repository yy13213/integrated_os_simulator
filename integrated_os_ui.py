import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from integrated_os_simulator import IntegratedScheduler, MemoryManager, ProcessState
from typing import List, Dict

def create_process_gantt_chart(execution_log: List[Dict]):
    """创建进程甘特图"""
    fig = go.Figure()
    
    # 为每个进程分配颜色
    process_colors = {}
    color_palette = px.colors.qualitative.Set3
    
    for i, entry in enumerate(execution_log):
        process_name = entry['process']
        if process_name not in process_colors:
            process_colors[process_name] = color_palette[len(process_colors) % len(color_palette)]
        
        # 添加进程执行条
        fig.add_trace(go.Bar(
            x=[1],  # 每个时间片的宽度
            y=[process_name],
            orientation='h',
            name=f"{process_name} (时间片 {entry['time']})",
            marker_color=process_colors[process_name],
            base=entry['time'],
            text=f"指令:{entry['execution_info']['executed_instructions']}<br>"
                 f"缺页:{entry['execution_info']['page_faults']}",
            textposition='inside',
            hovertemplate=f"<b>{process_name}</b><br>" +
                         f"时间片: {entry['time']}<br>" +
                         f"执行指令: {entry['execution_info']['executed_instructions']}<br>" +
                         f"缺页次数: {entry['execution_info']['page_faults']}<br>" +
                         f"状态: {entry['state']}<extra></extra>"
        ))
    
    fig.update_layout(
        title='进程调度甘特图',
        xaxis_title='时间片',
        yaxis_title='进程',
        height=400,
        showlegend=False,
        xaxis=dict(dtick=1)
    )
    
    return fig

def create_memory_usage_chart(execution_log: List[Dict]):
    """创建内存使用率图表"""
    times = []
    memory_usage = []
    process_counts = []
    
    for entry in execution_log:
        times.append(entry['time'])
        memory_usage.append(len(entry['memory_pages']))
        # 统计当前活跃进程数
        active_processes = sum(1 for log in execution_log 
                              if log['time'] == entry['time'] and log['state'] != 'E')
        process_counts.append(active_processes)
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('各进程内存使用页数', '活跃进程数量'),
        vertical_spacing=0.12
    )
    
    # 内存使用
    fig.add_trace(
        go.Scatter(x=times, y=memory_usage, mode='lines+markers',
                  name='内存页数', line=dict(color='blue', width=2)),
        row=1, col=1
    )
    
    # 活跃进程数
    fig.add_trace(
        go.Scatter(x=times, y=process_counts, mode='lines+markers',
                  name='活跃进程', line=dict(color='red', width=2)),
        row=2, col=1
    )
    
    fig.update_layout(height=500, title_text="系统资源使用情况")
    fig.update_xaxes(title_text="时间片", row=2, col=1)
    fig.update_yaxes(title_text="页数", row=1, col=1)
    fig.update_yaxes(title_text="进程数", row=2, col=1)
    
    return fig

def create_page_fault_analysis(execution_log: List[Dict]):
    """创建缺页分析图"""
    process_faults = {}
    time_faults = []
    
    for entry in execution_log:
        process_name = entry['process']
        faults = entry['execution_info']['page_faults']
        
        if process_name not in process_faults:
            process_faults[process_name] = 0
        process_faults[process_name] += faults
        
        time_faults.append({
            'time': entry['time'],
            'process': process_name,
            'faults': faults
        })
    
    # 创建双子图
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('各进程总缺页次数', '缺页时间分布'),
        specs=[[{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # 进程缺页统计
    processes = list(process_faults.keys())
    fault_counts = list(process_faults.values())
    
    fig.add_trace(
        go.Bar(x=processes, y=fault_counts, name='总缺页次数',
               marker_color='orange'),
        row=1, col=1
    )
    
    # 时间分布散点图
    df_faults = pd.DataFrame(time_faults)
    for process in processes:
        process_data = df_faults[df_faults['process'] == process]
        fig.add_trace(
            go.Scatter(x=process_data['time'], y=process_data['faults'],
                      mode='markers', name=f'{process}缺页',
                      marker_size=8),
            row=1, col=2
        )
    
    fig.update_layout(height=400, title_text="缺页分析")
    return fig

def main():
    st.set_page_config(
        page_title="操作系统综合实验平台",
        page_icon="🖥️",
        layout="wide"
    )
    
    st.title("🖥️ 操作系统综合实验平台")
    st.markdown("**融合进程调度与内存管理的仿真系统**")
    st.markdown("---")
    
    # 初始化会话状态
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = None
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'execution_log' not in st.session_state:
        st.session_state.execution_log = []
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    
    # 侧边栏配置
    with st.sidebar:
        st.header("🎛️ 实验配置")
        
        st.subheader("📊 系统参数")
        total_memory = st.slider("总内存页数", min_value=4, max_value=32, value=16, step=2)
        instructions_per_time = st.slider("每时间片指令数", min_value=1, max_value=20, value=5)
        time_quantum = st.slider("时间片大小", min_value=1, max_value=5, value=2)
        
        st.subheader("📋 进程配置")
        
        # 进程数量选择
        num_processes = st.selectbox("进程数量", options=[3, 4, 5, 6], index=2)
        
        # 动态生成进程配置
        process_configs = []
        for i in range(num_processes):
            with st.expander(f"进程 Q{i+1}"):
                required_time = st.slider(
                    f"Q{i+1} 要求运行时间", 
                    min_value=1, max_value=20, value=5+i, 
                    key=f"time_{i}"
                )
                memory_limit = st.slider(
                    f"Q{i+1} 内存限制(页)", 
                    min_value=2, max_value=16, value=8,
                    key=f"memory_{i}"
                )
                process_configs.append({
                    'name': f'Q{i+1}',
                    'required_time': required_time,
                    'memory_limit': memory_limit
                })
        
        st.subheader("🎮 控制")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 开始仿真", use_container_width=True):
                # 创建新的仿真实例
                memory_mgr = MemoryManager(total_memory_pages=total_memory)
                scheduler = IntegratedScheduler(memory_mgr)
                scheduler.instructions_per_time_unit = instructions_per_time
                scheduler.time_quantum = time_quantum
                
                # 添加进程
                for config in process_configs:
                    scheduler.add_process(
                        config['name'], 
                        config['required_time'],
                        config['memory_limit']
                    )
                
                st.session_state.scheduler = scheduler
                st.session_state.simulation_running = True
                st.session_state.execution_log = []
                st.session_state.current_step = 0
                st.success("仿真已启动！")
        
        with col2:
            if st.button("🔄 重置", use_container_width=True):
                st.session_state.scheduler = None
                st.session_state.simulation_running = False
                st.session_state.execution_log = []
                st.session_state.current_step = 0
                st.info("系统已重置")
        
        # 实时控制
        if st.session_state.scheduler:
            st.subheader("⏯️ 步进控制")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("▶️ 下一步"):
                    if st.session_state.simulation_running:
                        result = st.session_state.scheduler.run_time_slice()
                        if result.get('status') != 'no_ready_process':
                            st.session_state.execution_log.append(result)
                            st.session_state.current_step += 1
                        else:
                            st.session_state.simulation_running = False
                            st.success("所有进程已完成！")
                        st.rerun()
            
            with col2:
                if st.button("⏩ 运行到结束"):
                    if st.session_state.simulation_running:
                        while st.session_state.simulation_running:
                            result = st.session_state.scheduler.run_time_slice()
                            if result.get('status') != 'no_ready_process':
                                st.session_state.execution_log.append(result)
                                st.session_state.current_step += 1
                            else:
                                st.session_state.simulation_running = False
                                break
                        st.success("仿真完成！")
                        st.rerun()
            
            with col3:
                auto_run = st.checkbox("🔄 自动运行")
                if auto_run and st.session_state.simulation_running:
                    time.sleep(1)
                    result = st.session_state.scheduler.run_time_slice()
                    if result.get('status') != 'no_ready_process':
                        st.session_state.execution_log.append(result)
                        st.session_state.current_step += 1
                        st.rerun()
                    else:
                        st.session_state.simulation_running = False
                        st.success("仿真完成！")
    
    # 主显示区域
    if st.session_state.scheduler:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 实时状态", "📈 进程调度", "💾 内存管理", "🔍 详细分析", "📋 执行日志"
        ])
        
        with tab1:
            st.subheader("📊 系统实时状态")
            
            # 显示当前系统配置
            if st.session_state.scheduler:
                with st.expander("🔧 系统配置信息", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**总内存页数**: {st.session_state.scheduler.memory_manager.total_memory_pages}")
                        st.write(f"**时间片大小**: {st.session_state.scheduler.time_quantum}")
                    with col2:
                        st.write(f"**每时间片指令数**: {st.session_state.scheduler.instructions_per_time_unit}")
                        st.write(f"**进程数量**: {len(st.session_state.scheduler.processes)}")
                    with col3:
                        st.write(f"**当前时间**: {st.session_state.scheduler.current_time}")
                        st.write(f"**仿真状态**: {'运行中' if st.session_state.simulation_running else '已停止'}")
            
            if st.session_state.execution_log:
                # 当前系统状态
                col1, col2, col3, col4 = st.columns(4)
                
                latest_entry = st.session_state.execution_log[-1]
                
                with col1:
                    st.metric("当前时间片", st.session_state.current_step)
                with col2:
                    st.metric("当前进程", latest_entry['process'])
                with col3:
                    st.metric("本次执行指令", latest_entry['execution_info']['executed_instructions'])
                with col4:
                    st.metric("本次缺页", latest_entry['execution_info']['page_faults'])
                
                # 进程状态表
                st.subheader("进程状态表")
                process_stats = st.session_state.scheduler.get_process_statistics()
                
                status_data = []
                for name, stats in process_stats.items():
                    status_data.append({
                        '进程名': name,
                        '已运行时间': stats['executed_time'],
                        '要求运行时间': stats['required_time'],
                        '完成率': f"{stats['completion_rate']:.1%}",
                        '执行指令数': stats['executed_instructions'],
                        '总指令数': stats['total_instructions'],
                        '缺页次数': stats['page_faults'],
                        '状态': stats['state']
                    })
                
                df_status = pd.DataFrame(status_data)
                st.dataframe(df_status, use_container_width=True, hide_index=True)
                
                # 内存状态
                st.subheader("内存分配状态")
                memory_stats = st.session_state.scheduler.get_memory_statistics()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("内存利用率", f"{memory_stats['utilization_rate']:.1%}")
                with col2:
                    st.metric("已分配页数", f"{memory_stats['total_allocated']}/{memory_stats['total_capacity']}")
                with col3:
                    st.metric("空闲页数", memory_stats['free_pages'])
                
                # 内存分配可视化
                if memory_stats['allocated_by_process']:
                    memory_data = []
                    for pid, pages in memory_stats['allocated_by_process'].items():
                        process_name = f"Q{pid+1}"
                        memory_data.extend([{
                            '页号': page,
                            '进程': process_name,
                            '值': 1
                        } for page in pages])
                    
                    if memory_data:
                        df_memory = pd.DataFrame(memory_data)
                        fig_memory = px.bar(
                            df_memory, x='页号', y='值', color='进程',
                            title='内存页面分配状态',
                            height=300
                        )
                        fig_memory.update_layout(showlegend=True, yaxis_title="占用状态")
                        st.plotly_chart(fig_memory, use_container_width=True)
            
            else:
                st.info("请点击 '下一步' 开始仿真")
        
        with tab2:
            st.subheader("📈 进程调度分析")
            
            if st.session_state.execution_log:
                # 进程甘特图
                gantt_fig = create_process_gantt_chart(st.session_state.execution_log)
                st.plotly_chart(gantt_fig, use_container_width=True)
                
                # 进程完成情况
                st.subheader("进程完成情况")
                process_stats = st.session_state.scheduler.get_process_statistics()
                
                completion_data = []
                for name, stats in process_stats.items():
                    completion_data.append({
                        '进程': name,
                        '完成率': stats['completion_rate'],
                        '状态': stats['state']
                    })
                
                df_completion = pd.DataFrame(completion_data)
                fig_completion = px.bar(
                    df_completion, x='进程', y='完成率',
                    color='状态', title='进程完成率',
                    height=400
                )
                st.plotly_chart(fig_completion, use_container_width=True)
            
            else:
                st.info("暂无调度数据")
        
        with tab3:
            st.subheader("💾 内存管理分析")
            
            if st.session_state.execution_log:
                # 内存使用情况
                memory_fig = create_memory_usage_chart(st.session_state.execution_log)
                st.plotly_chart(memory_fig, use_container_width=True)
                
                # 缺页分析
                page_fault_fig = create_page_fault_analysis(st.session_state.execution_log)
                st.plotly_chart(page_fault_fig, use_container_width=True)
            
            else:
                st.info("暂无内存数据")
        
        with tab4:
            st.subheader("🔍 详细性能分析")
            
            if st.session_state.execution_log:
                # 综合性能指标
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**进程性能指标**")
                    process_stats = st.session_state.scheduler.get_process_statistics()
                    
                    total_page_faults = sum(stats['page_faults'] for stats in process_stats.values())
                    total_instructions = sum(stats['executed_instructions'] for stats in process_stats.values())
                    avg_completion = sum(stats['completion_rate'] for stats in process_stats.values()) / len(process_stats)
                    
                    st.metric("总缺页次数", total_page_faults)
                    st.metric("总执行指令数", total_instructions)
                    st.metric("平均完成率", f"{avg_completion:.1%}")
                
                with col2:
                    st.write("**系统性能指标**")
                    memory_stats = st.session_state.scheduler.get_memory_statistics()
                    
                    st.metric("内存利用率", f"{memory_stats['utilization_rate']:.1%}")
                    st.metric("平均缺页率", f"{total_page_faults/total_instructions:.3f}" if total_instructions > 0 else "0")
                    
                    # 修复时间片利用率计算
                    if st.session_state.current_step > 0 and len(st.session_state.execution_log) > 0:
                        utilization_rate = len(st.session_state.execution_log) / st.session_state.current_step
                        st.metric("时间片利用率", f"{utilization_rate:.1%}")
                    else:
                        st.metric("时间片利用率", "0.0%")
                
                # 性能趋势分析
                if len(st.session_state.execution_log) > 1:
                    st.subheader("性能趋势分析")
                    
                    # 累积缺页趋势
                    cumulative_faults = []
                    cumulative_instructions = []
                    fault_rate_trend = []
                    
                    total_faults = 0
                    total_instr = 0
                    
                    for entry in st.session_state.execution_log:
                        total_faults += entry['execution_info']['page_faults']
                        total_instr += entry['execution_info']['executed_instructions']
                        
                        cumulative_faults.append(total_faults)
                        cumulative_instructions.append(total_instr)
                        fault_rate_trend.append(total_faults / total_instr if total_instr > 0 else 0)
                    
                    times = list(range(len(st.session_state.execution_log)))
                    
                    fig_trend = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('累积缺页次数', '缺页率趋势'),
                        vertical_spacing=0.1
                    )
                    
                    fig_trend.add_trace(
                        go.Scatter(x=times, y=cumulative_faults, mode='lines+markers',
                                  name='累积缺页', line=dict(color='red')),
                        row=1, col=1
                    )
                    
                    fig_trend.add_trace(
                        go.Scatter(x=times, y=fault_rate_trend, mode='lines+markers',
                                  name='缺页率', line=dict(color='blue')),
                        row=2, col=1
                    )
                    
                    fig_trend.update_layout(height=500, title_text="系统性能趋势")
                    st.plotly_chart(fig_trend, use_container_width=True)
            
            else:
                st.info("暂无分析数据")
        
        with tab5:
            st.subheader("📋 详细执行日志")
            
            if st.session_state.execution_log:
                # 日志筛选
                col1, col2 = st.columns(2)
                with col1:
                    show_only_faults = st.checkbox("只显示有缺页的时间片")
                with col2:
                    selected_process = st.selectbox(
                        "筛选进程",
                        options=['全部'] + [f'Q{i+1}' for i in range(num_processes)]
                    )
                
                # 构建日志表
                log_data = []
                for entry in st.session_state.execution_log:
                    # 应用筛选
                    if show_only_faults and entry['execution_info']['page_faults'] == 0:
                        continue
                    if selected_process != '全部' and entry['process'] != selected_process:
                        continue
                    
                    log_data.append({
                        '时间片': entry['time'],
                        '进程': entry['process'],
                        '已运行时间': entry['executed_time'],
                        '要求时间': entry['required_time'],
                        '执行指令数': entry['execution_info']['executed_instructions'],
                        '缺页次数': entry['execution_info']['page_faults'],
                        '访问页面': str(entry['execution_info']['accessed_pages'][:5]) + '...' if len(entry['execution_info']['accessed_pages']) > 5 else str(entry['execution_info']['accessed_pages']),
                        '分配页面': str(entry['memory_pages']),
                        '状态': entry['state']
                    })
                
                if log_data:
                    df_log = pd.DataFrame(log_data)
                    st.dataframe(df_log, use_container_width=True, height=400)
                    
                    # 导出功能
                    csv = df_log.to_csv(index=False)
                    st.download_button(
                        label="📥 下载执行日志",
                        data=csv,
                        file_name=f"integrated_os_log_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("没有符合筛选条件的日志记录")
            
            else:
                st.info("暂无执行日志")
    
    else:
        st.info("👈 请在左侧配置实验参数并点击 '开始仿真' 按钮")
    
    # 底部说明
    st.markdown("---")
    st.markdown("""
    ### 📖 实验说明
    
    #### 🎯 实验特色
    - **融合仿真**: 同时模拟进程调度和内存管理
    - **可调参数**: 可设置每时间片执行的指令数量
    - **实时可视化**: 动态展示系统状态变化
    - **详细分析**: 提供多维度的性能分析
    
    #### ⚙️ 核心机制
    - **时间片轮转**: 进程按时间片轮转执行
    - **指令执行**: 每个时间片执行指定数量的指令
    - **内存管理**: 采用LRU页面置换算法
    - **地址转换**: 指令地址自动转换为页地址
    
    #### 📊 关键指标
    - **进程完成率**: 显示各进程的执行进度
    - **缺页次数**: 统计内存管理的效率
    - **内存利用率**: 反映内存分配的合理性
    - **系统吞吐量**: 衡量整体系统性能
    
    #### 💡 操作提示
    1. 调整左侧参数配置系统环境
    2. 点击"开始仿真"初始化系统
    3. 使用"下一步"逐步观察执行过程
    4. 查看各标签页了解不同方面的系统状态
    5. 下载执行日志进行深入分析
    """)

if __name__ == "__main__":
    main() 