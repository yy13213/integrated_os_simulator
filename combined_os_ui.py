import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from typing import List, Dict, Optional

# 导入两个模块的功能
from memory_management import MemoryManager, InstructionGenerator
from processor_scheduling import PCB as SchedulerPCB, ProcessScheduler

class CombinedSystemUI:
    """融合系统界面"""
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.process_scheduler = ProcessScheduler()
        self.instruction_generator = InstructionGenerator()
        
    def initialize_session_state(self):
        """初始化会话状态"""
        # 进程调度状态
        if 'scheduler' not in st.session_state:
            st.session_state.scheduler = ProcessScheduler()
        if 'auto_run_scheduler' not in st.session_state:
            st.session_state.auto_run_scheduler = False
        if 'step_delay' not in st.session_state:
            st.session_state.step_delay = 1.0
        
        # 内存管理状态
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

def create_memory_visualization(memory_states: List[List[int]], memory_size: int):
    """创建内存状态可视化"""
    if not memory_states:
        return None
        
    fig = go.Figure()
    
    # 获取最后一个内存状态
    current_memory = memory_states[-1]
    
    # 创建内存槽位可视化
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
    
    return fig

def create_process_status_chart(processes: List):
    """创建进程状态图表"""
    if not processes:
        return None
        
    data = []
    for process in processes:
        progress = min(process.run_time / process.require_time * 100, 100) if process.require_time > 0 else 100
        status_emoji = "✅" if process.status == 'E' else "🔄"
        
        data.append({
            "进程名": process.name,
            "要求运行时间": process.require_time,
            "已运行时间": process.run_time,
            "进度": progress,
            "状态": f"{status_emoji} {'完成' if process.status == 'E' else '就绪'}",
        })
    
    df = pd.DataFrame(data)
    
    # 创建进度图
    fig = px.bar(
        df, 
        x='进程名', 
        y='进度',
        title='进程执行进度',
        text='进度',
        color='进度',
        color_continuous_scale='RdYlGn'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(height=300, yaxis_title='完成百分比 (%)')
    
    return fig

def main():
    st.set_page_config(
        page_title="操作系统融合实验平台", 
        page_icon="🖥️", 
        layout="wide"
    )
    
    st.title("🖥️ 操作系统融合实验平台")
    st.markdown("**进程调度 + 内存管理 综合仿真系统**")
    st.markdown("---")
    
    # 初始化系统
    system_ui = CombinedSystemUI()
    system_ui.initialize_session_state()
    
    # 侧边栏控制面板
    with st.sidebar:
        st.header("🎛️ 系统控制中心")
        
        # 选择实验模式
        experiment_mode = st.selectbox(
            "选择实验模式",
            options=["同时运行", "独立调试"],
            help="同时运行：两个系统协同工作；独立调试：分别测试各模块"
        )
        
        st.markdown("---")
        
        # 进程调度配置
        st.subheader("⚙️ 进程调度配置")
        
        scheduler_active = st.checkbox("启用进程调度器", value=True)
        
        if scheduler_active:
            st.write("**进程运行时间配置**")
            process_times = []
            for i in range(1, 6):
                time_val = st.number_input(
                    f"进程 Q{i} 运行时间", 
                    min_value=0, 
                    max_value=20, 
                    value=0 if i > 3 else 3+i,  # 默认前3个进程有运行时间
                    key=f"scheduler_process_{i}"
                )
                process_times.append(time_val)
            
            # 调度控制
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🆕 创建进程", use_container_width=True, key="create_processes"):
                    st.session_state.scheduler = ProcessScheduler()
                    st.session_state.scheduler.create_processes_with_times(process_times)
                    st.session_state.auto_run_scheduler = False
                    st.success("进程已创建！")
                    st.rerun()
            
            with col2:
                if st.button("🔄 重置调度", use_container_width=True, key="reset_scheduler"):
                    st.session_state.scheduler = ProcessScheduler()
                    st.session_state.auto_run_scheduler = False
                    st.info("调度器已重置")
                    st.rerun()
            
            # 执行控制
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ 调度一步", use_container_width=True, key="step_scheduler"):
                    if st.session_state.scheduler.process_count > 0:
                        st.session_state.scheduler.run_one_step()
                        st.rerun()
            
            with col2:
                if not st.session_state.auto_run_scheduler:
                    if st.button("🚀 自动调度", use_container_width=True, key="auto_scheduler"):
                        if st.session_state.scheduler.process_count > 0:
                            st.session_state.auto_run_scheduler = True
                            st.rerun()
                else:
                    if st.button("⏸️ 暂停调度", use_container_width=True, key="pause_scheduler"):
                        st.session_state.auto_run_scheduler = False
                        st.rerun()
            
            st.session_state.step_delay = st.slider(
                "调度速度 (秒)", 
                min_value=0.1, 
                max_value=3.0, 
                value=st.session_state.step_delay,
                step=0.1,
                key="scheduler_delay"
            )
        
        st.markdown("---")
        
        # 内存管理配置
        st.subheader("💾 内存管理配置")
        
        memory_active = st.checkbox("启用内存管理器", value=True)
        
        if memory_active:
            algorithm = st.selectbox(
                "页面置换算法",
                options=['FIFO', 'LRU', 'OPT', 'LFR'],
                index=1,
                key="memory_algorithm",
                help="FIFO: 先进先出\nLRU: 最近最少使用\nOPT: 最佳淘汰算法\nLFR: 最少访问页面算法"
            )
            
            memory_size = st.slider(
                "内存容量（页数）",
                min_value=4,
                max_value=32,
                value=8,
                step=2,
                key="memory_size",
                help="可选择4到32页的内存容量"
            )
            
            # 内存控制
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 生成指令序列", use_container_width=True, key="generate_instructions"):
                    generator = InstructionGenerator()
                    st.session_state.instructions = generator.generate_instructions()
                    st.session_state.simulation_result = None
                    st.session_state.current_step = 0
                    st.session_state.is_simulating = False
                    st.success("指令序列已生成！")
            
            with col2:
                if st.button("📊 开始内存仿真", use_container_width=True, key="start_memory_sim"):
                    if st.session_state.instructions is not None:
                        result = st.session_state.memory_manager.simulate(
                            algorithm, memory_size, st.session_state.instructions
                        )
                        st.session_state.simulation_result = result
                        st.session_state.current_step = 0
                        st.session_state.is_simulating = True
                        st.success("内存仿真开始！")
                    else:
                        st.error("请先生成指令序列！")
            
            # 内存步进控制
            if st.session_state.simulation_result:
                max_steps = len(st.session_state.simulation_result['access_log'])
                
                step = st.slider(
                    "内存仿真步骤",
                    min_value=0,
                    max_value=max_steps,
                    value=st.session_state.current_step,
                    key="memory_step",
                    help=f"总共{max_steps}个访问步骤"
                )
                st.session_state.current_step = step
    
    # 主显示区域
    if experiment_mode == "同时运行":
        # 并排显示两个系统
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ 进程调度系统")
            
            if scheduler_active and st.session_state.scheduler.process_count > 0:
                # 显示进程状态
                processes = st.session_state.scheduler.get_all_processes()
                
                if processes:
                    # 进程状态表
                    data = []
                    for process in processes:
                        progress = min(process.run_time / process.require_time * 100, 100) if process.require_time > 0 else 100
                        status_emoji = "✅" if process.status == 'E' else "🔄"
                        
                        data.append({
                            "进程名": process.name,
                            "要求时间": process.require_time,
                            "已运行": process.run_time,
                            "进度": f"{progress:.1f}%",
                            "状态": f"{status_emoji} {'完成' if process.status == 'E' else '就绪'}",
                        })
                    
                    df = pd.DataFrame(data)
                    
                    # 高亮当前运行的进程
                    def highlight_current(row):
                        if (st.session_state.scheduler.current and 
                            row['进程名'] == st.session_state.scheduler.current.name and 
                            row['状态'].endswith('就绪')):
                            return ['background-color: #ffeb3b; font-weight: bold'] * len(row)
                        elif row['状态'].endswith('完成'):
                            return ['background-color: #c8e6c9'] * len(row)
                        return [''] * len(row)
                    
                    styled_df = df.style.apply(highlight_current, axis=1)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    # 进程状态图表
                    process_chart = create_process_status_chart(processes)
                    if process_chart:
                        st.plotly_chart(process_chart, use_container_width=True)
                    
                    # 当前调度信息
                    if st.session_state.scheduler.current:
                        st.info(f"🎯 当前调度: **{st.session_state.scheduler.current.name}** | 调度轮次: **{st.session_state.scheduler.round_count}**")
                    elif st.session_state.scheduler.round_count > 0:
                        st.success("🎉 所有进程调度完成！")
                    
                    # 统计信息
                    if st.session_state.scheduler.execution_log:
                        st.write("**调度统计**")
                        total_rounds = st.session_state.scheduler.round_count
                        completed_processes = len([log for log in st.session_state.scheduler.execution_log if log['action'] == '完成'])
                        remaining_processes = st.session_state.scheduler.process_count
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("总轮次", total_rounds)
                        with col2:
                            st.metric("已完成", completed_processes)
                        with col3:
                            st.metric("剩余进程", remaining_processes)
            
            else:
                st.info("请在左侧配置进程运行时间并点击'创建进程'")
        
        with col2:
            st.subheader("💾 内存管理系统")
            
            if memory_active and st.session_state.simulation_result and st.session_state.current_step > 0:
                result = st.session_state.simulation_result
                current_step = st.session_state.current_step
                
                # 当前状态信息
                current_log = result['access_log'][:current_step]
                current_faults = sum(1 for log in current_log if log['is_fault'])
                current_hit_rate = 1 - (current_faults / current_step) if current_step > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("当前步骤", f"{current_step}/{len(result['access_log'])}")
                with col2:
                    st.metric("累计缺页", current_faults)
                with col3:
                    st.metric("命中率", f"{current_hit_rate:.3f}")
                
                # 内存状态可视化
                if current_step > 0:
                    memory_states = []
                    for i in range(current_step):
                        memory_states.append(result['access_log'][i]['memory_after'])
                    
                    memory_fig = create_memory_visualization(memory_states, memory_size)
                    if memory_fig:
                        st.plotly_chart(memory_fig, use_container_width=True)
                    
                    # 当前内存详情
                    current_memory = result['access_log'][current_step-1]['memory_after']
                    current_page = result['access_log'][current_step-1]['page']
                    
                    st.write("**内存详情**")
                    st.write(f"当前访问页面: {current_page}")
                    st.write(f"内存状态: {current_memory}")
                
                # 最近访问历史
                st.write("**最近访问历史**")
                recent_steps = max(0, current_step - 5)
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
                
                if not log_df.empty:
                    st.dataframe(log_df, use_container_width=True, hide_index=True)
            
            else:
                st.info("请在左侧生成指令序列并开始内存仿真")
    
    else:  # 独立调试模式
        tab1, tab2 = st.tabs(["⚙️ 进程调度器", "💾 内存管理器"])
        
        with tab1:
            st.subheader("进程调度器独立测试")
            
            if scheduler_active:
                # 显示完整的调度器界面
                if st.session_state.scheduler.process_count > 0 or st.session_state.scheduler.execution_log:
                    processes = st.session_state.scheduler.get_all_processes()
                    
                    if processes:
                        # 进程状态表
                        data = []
                        for process in processes:
                            progress = min(process.run_time / process.require_time * 100, 100) if process.require_time > 0 else 100
                            status_emoji = "✅" if process.status == 'E' else "🔄"
                            
                            data.append({
                                "进程名": process.name,
                                "要求运行时间": process.require_time,
                                "已运行时间": process.run_time,
                                "进度": f"{progress:.1f}%",
                                "状态": f"{status_emoji} {'完成' if process.status == 'E' else '就绪'}",
                            })
                        
                        df = pd.DataFrame(data)
                        
                        # 高亮当前运行的进程
                        def highlight_current(row):
                            if (st.session_state.scheduler.current and 
                                row['进程名'] == st.session_state.scheduler.current.name and 
                                row['状态'].endswith('就绪')):
                                return ['background-color: #ffeb3b; font-weight: bold'] * len(row)
                            elif row['状态'].endswith('完成'):
                                return ['background-color: #c8e6c9'] * len(row)
                            return [''] * len(row)
                        
                        styled_df = df.style.apply(highlight_current, axis=1)
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)
                        
                        # 进程状态图表
                        process_chart = create_process_status_chart(processes)
                        if process_chart:
                            st.plotly_chart(process_chart, use_container_width=True)
                        
                        # 统计信息
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.session_state.scheduler.current:
                                st.info(f"🎯 当前调度: **{st.session_state.scheduler.current.name}**")
                            elif st.session_state.scheduler.round_count > 0:
                                st.success("🎉 所有进程调度完成！")
                        
                        with col2:
                            if st.session_state.scheduler.execution_log:
                                total_rounds = st.session_state.scheduler.round_count
                                completed_processes = len([log for log in st.session_state.scheduler.execution_log if log['action'] == '完成'])
                                
                                st.metric("总调度轮次", total_rounds)
                                st.metric("已完成进程", completed_processes)
                        
                        # 执行日志
                        if st.session_state.scheduler.execution_log:
                            st.subheader("📝 执行日志")
                            
                            recent_logs = st.session_state.scheduler.execution_log[-5:]
                            log_data = []
                            
                            for log in recent_logs:
                                action_emoji = "🏁" if log['action'] == '完成' else "▶️"
                                log_data.append({
                                    "轮次": log['round'],
                                    "选中进程": log['selected_process'],
                                    "动作": f"{action_emoji} {log['action']}",
                                    "运行时间": f"{log['run_time_before']} → {log['run_time']}",
                                    "总需求": log['require_time']
                                })
                            
                            if log_data:
                                log_df = pd.DataFrame(log_data)
                                st.dataframe(log_df, use_container_width=True, hide_index=True)
                
                else:
                    st.info("请在左侧配置进程运行时间并点击'创建进程'")
            else:
                st.info("请在左侧启用进程调度器")
        
        with tab2:
            st.subheader("内存管理器独立测试")
            
            if memory_active:
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
                    
                    # 当前内存仿真步进显示
                    if st.session_state.current_step > 0:
                        st.subheader("内存仿真步进")
                        current_step = st.session_state.current_step
                        current_log = result['access_log'][:current_step]
                        
                        # 最近的内存状态
                        if current_log:
                            memory_states = [log['memory_after'] for log in current_log]
                            memory_fig = create_memory_visualization(memory_states, memory_size)
                            if memory_fig:
                                st.plotly_chart(memory_fig, use_container_width=True)
                        
                        # 详细日志表
                        st.subheader("详细访问日志")
                        log_data = []
                        for i, log in enumerate(current_log[-10:], start=max(0, current_step-10)):
                            log_data.append({
                                '步骤': i + 1,
                                '访问页面': log['page'],
                                '操作结果': log['action'],
                                '是否缺页': '是' if log['is_fault'] else '否',
                                '访问后内存': str(log['memory_after'])
                            })
                        
                        if log_data:
                            log_df = pd.DataFrame(log_data)
                            st.dataframe(log_df, use_container_width=True, hide_index=True)
                
                else:
                    st.info("请在左侧生成指令序列并开始内存仿真")
            else:
                st.info("请在左侧启用内存管理器")
    
    # 自动执行逻辑
    if (scheduler_active and st.session_state.auto_run_scheduler and 
        st.session_state.scheduler.process_count > 0):
        time.sleep(st.session_state.step_delay)
        st.session_state.scheduler.run_one_step()
        
        if st.session_state.scheduler.is_completed():
            st.session_state.auto_run_scheduler = False
            st.success("🎉 进程调度完成！")
        
        st.rerun()
    
    # 底部说明
    st.markdown("---")
    st.markdown("""
    ### 📖 融合系统使用说明
    
    #### 🎯 系统特色
    - **双系统融合**: 同时运行进程调度和内存管理
    - **独立调试**: 可分别测试各个子系统
    - **实时同步**: 两个系统状态实时更新
    - **可视化分析**: 多维度图表展示系统状态
    
    #### ⚙️ 操作步骤
    1. **选择模式**: 选择"同时运行"或"独立调试"
    2. **配置参数**: 设置进程运行时间和内存参数
    3. **启动系统**: 分别启动进程调度和内存管理
    4. **观察运行**: 查看实时状态和性能指标
    5. **分析结果**: 通过图表分析系统性能
    
    #### 💡 实验建议
    - 先在独立调试模式下熟悉各子系统
    - 在同时运行模式下观察系统协同效果
    - 尝试不同参数组合，比较系统性能
    - 关注缺页率和调度效率的关系
    """)

# 扩展ProcessScheduler类以支持自定义运行时间
class ProcessScheduler:
    """进程调度器"""
    def __init__(self):
        self.current = None
        self.process_count = 0
        self.round_count = 0
        self.execution_log = []
        self.is_running = False
        self.is_paused = False
        
    def create_processes_with_times(self, process_times: List[int]) -> None:
        """使用指定运行时间创建进程"""
        processes = []
        for i, require_time in enumerate(process_times, 1):
            if require_time > 0:
                process = SchedulerPCB(f"Q{i}", require_time)
                processes.append(process)
        
        if not processes:
            return
            
        # 构建循环队列
        for i in range(len(processes)):
            processes[i].next = processes[(i + 1) % len(processes)]
        
        self.current = processes[0]
        self.process_count = len(processes)
        self.round_count = 0
        self.execution_log = []
        self.is_running = False
        self.is_paused = False
    
    def get_all_processes(self) -> List[SchedulerPCB]:
        """获取所有进程"""
        if self.current is None:
            return []
        
        processes = []
        temp = self.current
        start_process = self.current
        
        while True:
            processes.append(temp)
            temp = temp.next
            if temp == start_process:
                break
        
        # 添加已完成的进程
        completed_processes = {}
        for log in self.execution_log:
            if log['status'] == 'E' and log['process_name'] not in [p.name for p in processes]:
                if log['process_name'] not in completed_processes:
                    completed_processes[log['process_name']] = {
                        'name': log['process_name'],
                        'require_time': log['require_time'],
                        'run_time': log['run_time'],
                        'status': 'E'
                    }
        
        all_processes = []
        for p in processes:
            all_processes.append(p)
        
        for name, data in completed_processes.items():
            completed_pcb = SchedulerPCB(data['name'], data['require_time'])
            completed_pcb.run_time = data['run_time']
            completed_pcb.status = data['status']
            all_processes.append(completed_pcb)
        
        all_processes.sort(key=lambda x: x.name)
        return all_processes
    
    def run_one_step(self) -> bool:
        """执行一个调度步骤"""
        if self.current is None or self.process_count == 0:
            return False
        
        self.round_count += 1
        current_process = self.current
        
        log_entry = {
            'round': self.round_count,
            'selected_process': current_process.name,
            'process_name': current_process.name,
            'require_time': current_process.require_time,
            'run_time_before': current_process.run_time,
            'run_time': current_process.run_time + 1,
            'status': current_process.status,
            'action': '运行'
        }
        
        current_process.run_time += 1
        
        if current_process.run_time >= current_process.require_time:
            current_process.status = 'E'
            log_entry['status'] = 'E'
            log_entry['action'] = '完成'
            
            if self.process_count == 1:
                self.current = None
                self.process_count = 0
            else:
                prev = current_process
                while prev.next != current_process:
                    prev = prev.next
                
                prev.next = current_process.next
                self.current = current_process.next
                self.process_count -= 1
        else:
            self.current = current_process.next
        
        self.execution_log.append(log_entry)
        return True
    
    def is_completed(self) -> bool:
        """检查所有进程是否完成"""
        return self.process_count == 0

if __name__ == "__main__":
    main() 