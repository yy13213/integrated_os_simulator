import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from typing import List, Dict, Optional, Tuple
import random

# 导入两个模块的功能
from memory_management import MemoryManager, InstructionGenerator
from processor_scheduling import PCB as SchedulerPCB

class EnhancedProcess:
    """增强的进程类，支持指令级仿真"""
    def __init__(self, name: str, total_instructions: int, priority: int = 0):
        self.name = name
        self.total_instructions = total_instructions
        self.executed_instructions = 0
        self.priority = priority
        self.status = 'R'  # R=就绪, E=结束, B=阻塞
        self.start_time = 0
        self.end_time = 0
        self.execution_history = []  # 记录执行历史
        self.memory_pages = []  # 占用的内存页面
        self.next = None
        
        # 生成该进程的指令序列
        self.instruction_sequence = self._generate_instructions()
        
    def _generate_instructions(self) -> List[int]:
        """为进程生成指令序列（页面访问序列）"""
        # 基于局部性原理生成指令序列
        pages = []
        current_page = random.randint(0, 15)  # 起始页面
        
        for i in range(self.total_instructions):
            # 80%概率访问当前页面附近的页面（局部性原理）
            if random.random() < 0.8:
                # 在当前页面±2范围内选择
                offset = random.randint(-2, 2)
                next_page = max(0, min(15, current_page + offset))
            else:
                # 20%概率跳转到远程页面
                next_page = random.randint(0, 15)
            
            pages.append(next_page)
            current_page = next_page
            
        return pages
    
    def execute_instructions(self, count: int) -> List[int]:
        """执行指定数量的指令，返回访问的页面序列"""
        if self.is_completed():
            return []
            
        executed_pages = []
        for _ in range(min(count, self.total_instructions - self.executed_instructions)):
            page = self.instruction_sequence[self.executed_instructions]
            executed_pages.append(page)
            self.executed_instructions += 1
            
        return executed_pages
    
    def is_completed(self) -> bool:
        """检查进程是否完成"""
        return self.executed_instructions >= self.total_instructions
    
    def get_progress(self) -> float:
        """获取进程完成进度"""
        if self.total_instructions == 0:
            return 100.0
        return (self.executed_instructions / self.total_instructions) * 100

class IntegratedSimulator:
    """集成仿真器 - 结合进程调度和内存管理"""
    
    def __init__(self):
        self.processes = []
        self.current_process_index = 0
        self.current_time = 0
        self.time_quantum = 2  # 时间片大小
        self.instructions_per_time_unit = 5  # 每时间片运行的指令数
        self.memory_manager = MemoryManager()
        self.memory_size = 8
        self.algorithm = 'LRU'
        
        # 仿真记录
        self.execution_log = []
        self.gantt_data = []
        self.memory_stats = []
        
    def add_process(self, name: str, total_instructions: int, priority: int = 0):
        """添加进程"""
        process = EnhancedProcess(name, total_instructions, priority)
        self.processes.append(process)
        
    def configure_system(self, time_quantum: int, instructions_per_time_unit: int, 
                        memory_size: int, algorithm: str):
        """配置系统参数"""
        self.time_quantum = time_quantum
        self.instructions_per_time_unit = instructions_per_time_unit
        self.memory_size = memory_size
        self.algorithm = algorithm
        
    def run_simulation(self) -> Dict:
        """运行完整仿真"""
        self.current_time = 0
        self.execution_log = []
        self.gantt_data = []
        self.memory_stats = []
        
        # 初始化内存管理器
        self.memory_manager = MemoryManager()
        
        # 记录开始时间
        for process in self.processes:
            process.start_time = self.current_time
            process.status = 'R'
            process.executed_instructions = 0
        
        # 执行时间片轮转调度
        while not self._all_processes_completed():
            current_process = self._get_current_process()
            
            if current_process is None:
                break
                
            # 记录甘特图数据
            start_time = self.current_time
            
            # 执行时间片
            instructions_to_execute = self.time_quantum * self.instructions_per_time_unit
            executed_pages = current_process.execute_instructions(instructions_to_execute)
            
            # 处理内存访问
            page_faults = 0
            for page in executed_pages:
                # 模拟内存访问
                result = self._simulate_memory_access(page)
                if result['is_fault']:
                    page_faults += 1
            
            # 更新时间
            self.current_time += self.time_quantum
            
            # 记录执行日志
            log_entry = {
                'time': start_time,
                'process': current_process.name,
                'instructions_executed': len(executed_pages),
                'page_faults': page_faults,
                'progress': current_process.get_progress(),
                'status': 'completed' if current_process.is_completed() else 'running'
            }
            self.execution_log.append(log_entry)
            
            # 记录甘特图数据
            gantt_entry = {
                'Process': current_process.name,
                'Start': start_time,
                'Finish': self.current_time,
                'Duration': self.time_quantum,
                'Instructions': len(executed_pages),
                'Page_Faults': page_faults
            }
            self.gantt_data.append(gantt_entry)
            
            # 记录内存统计
            memory_stat = {
                'time': self.current_time,
                'process': current_process.name,
                'page_faults': page_faults,
                'memory_usage': len(self._get_current_memory_state())
            }
            self.memory_stats.append(memory_stat)
            
            # 检查进程是否完成
            if current_process.is_completed():
                current_process.status = 'E'
                current_process.end_time = self.current_time
            
            # 切换到下一个进程
            self._switch_to_next_process()
        
        return self._generate_simulation_report()
    
    def _simulate_memory_access(self, page: int) -> Dict:
        """模拟内存访问"""
        # 简化的内存访问模拟
        current_memory = self._get_current_memory_state()
        
        if page in current_memory:
            # 命中
            return {'is_fault': False, 'action': 'hit'}
        else:
            # 缺页
            if len(current_memory) < self.memory_size:
                current_memory.append(page)
            else:
                # 需要页面置换
                if self.algorithm == 'LRU':
                    current_memory.pop(0)  # 移除最近最少使用的
                elif self.algorithm == 'FIFO':
                    current_memory.pop(0)  # 移除最先进入的
                current_memory.append(page)
            
            return {'is_fault': True, 'action': 'fault'}
    
    def _get_current_memory_state(self) -> List[int]:
        """获取当前内存状态"""
        if not hasattr(self, '_current_memory'):
            self._current_memory = []
        return self._current_memory
    
    def _get_current_process(self) -> Optional[EnhancedProcess]:
        """获取当前要执行的进程"""
        if not self.processes:
            return None
            
        # 找到下一个未完成的进程
        for _ in range(len(self.processes)):
            process = self.processes[self.current_process_index]
            if not process.is_completed():
                return process
            self.current_process_index = (self.current_process_index + 1) % len(self.processes)
        
        return None
    
    def _switch_to_next_process(self):
        """切换到下一个进程"""
        self.current_process_index = (self.current_process_index + 1) % len(self.processes)
    
    def _all_processes_completed(self) -> bool:
        """检查所有进程是否完成"""
        return all(process.is_completed() for process in self.processes)
    
    def _generate_simulation_report(self) -> Dict:
        """生成仿真报告"""
        total_time = self.current_time
        total_instructions = sum(process.total_instructions for process in self.processes)
        total_page_faults = sum(log['page_faults'] for log in self.execution_log)
        
        return {
            'total_time': total_time,
            'total_instructions': total_instructions,
            'total_page_faults': total_page_faults,
            'page_fault_rate': total_page_faults / total_instructions if total_instructions > 0 else 0,
            'throughput': len(self.processes) / total_time if total_time > 0 else 0,
            'processes': [{
                'name': p.name,
                'total_instructions': p.total_instructions,
                'completion_time': p.end_time,
                'turnaround_time': p.end_time - p.start_time
            } for p in self.processes],
            'execution_log': self.execution_log,
            'gantt_data': self.gantt_data,
            'memory_stats': self.memory_stats
        }

def create_gantt_chart(gantt_data: List[Dict]) -> go.Figure:
    """创建甘特图"""
    if not gantt_data:
        return None
    
    df = pd.DataFrame(gantt_data)
    
    # 创建甘特图
    fig = px.timeline(
        df, 
        x_start="Start", 
        x_end="Finish", 
        y="Process",
        color="Process",
        title="进程调度甘特图",
        hover_data=["Instructions", "Page_Faults"]
    )
    
    # 添加注释显示指令数和缺页数
    for i, row in df.iterrows():
        fig.add_annotation(
            x=row['Start'] + row['Duration']/2,
            y=row['Process'],
            text=f"指令:{row['Instructions']}<br>缺页:{row['Page_Faults']}",
            showarrow=False,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="white",
            borderwidth=1
        )
    
    fig.update_layout(
        height=400,
        xaxis_title="时间",
        yaxis_title="进程"
    )
    
    return fig

def create_memory_fault_chart(memory_stats: List[Dict]) -> go.Figure:
    """创建内存缺页统计图"""
    if not memory_stats:
        return None
    
    df = pd.DataFrame(memory_stats)
    
    fig = go.Figure()
    
    # 按进程分组绘制缺页数
    for process in df['process'].unique():
        process_data = df[df['process'] == process]
        fig.add_trace(go.Scatter(
            x=process_data['time'],
            y=process_data['page_faults'].cumsum(),
            mode='lines+markers',
            name=f'{process} 累计缺页',
            line=dict(width=3)
        ))
    
    fig.update_layout(
        title="进程内存缺页统计",
        xaxis_title="时间",
        yaxis_title="累计缺页数",
        height=400
    )
    
    return fig

def create_system_performance_chart(simulation_report: Dict) -> go.Figure:
    """创建系统性能分析图"""
    processes_data = simulation_report['processes']
    
    if not processes_data:
        return None
    
    df = pd.DataFrame(processes_data)
    
    # 创建子图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['进程完成时间', '周转时间', '指令分布', '系统效率'],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 进程完成时间
    fig.add_trace(
        go.Bar(x=df['name'], y=df['completion_time'], name='完成时间'),
        row=1, col=1
    )
    
    # 周转时间
    fig.add_trace(
        go.Bar(x=df['name'], y=df['turnaround_time'], name='周转时间'),
        row=1, col=2
    )
    
    # 指令分布
    fig.add_trace(
        go.Pie(labels=df['name'], values=df['total_instructions'], name='指令分布'),
        row=2, col=1
    )
    
    # 系统效率指标
    efficiency_data = {
        '吞吐量': simulation_report['throughput'],
        '缺页率': simulation_report['page_fault_rate'],
        '平均周转时间': df['turnaround_time'].mean() / simulation_report['total_time']
    }
    
    fig.add_trace(
        go.Bar(x=list(efficiency_data.keys()), y=list(efficiency_data.values()), name='系统效率'),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False)
    
    return fig

def main():
    st.set_page_config(
        page_title="增强版操作系统融合实验平台", 
        page_icon="🚀", 
        layout="wide"
    )
    
    st.title("🚀 增强版操作系统融合实验平台")
    st.markdown("**进程调度 + 内存管理 + 仿真测试 综合系统**")
    st.markdown("---")
    
    # 初始化会话状态
    if 'simulator' not in st.session_state:
        st.session_state.simulator = IntegratedSimulator()
    if 'simulation_report' not in st.session_state:
        st.session_state.simulation_report = None
    
    # 侧边栏配置
    with st.sidebar:
        st.header("🎛️ 仿真配置中心")
        
        # 系统参数配置
        st.subheader("⚙️ 系统参数")
        
        time_quantum = st.slider(
            "时间片大小",
            min_value=1,
            max_value=10,
            value=2,
            help="每个进程连续执行的时间片长度"
        )
        
        instructions_per_time_unit = st.slider(
            "每时间片指令数",
            min_value=1,
            max_value=20,
            value=5,
            help="每个时间片内执行的指令数量"
        )
        
        memory_size = st.slider(
            "内存容量（页数）",
            min_value=4,
            max_value=32,
            value=8,
            help="系统总内存页数"
        )
        
        algorithm = st.selectbox(
            "页面置换算法",
            options=['FIFO', 'LRU', 'OPT'],
            index=1,
            help="选择页面置换算法"
        )
        
        st.markdown("---")
        
        # 进程配置
        st.subheader("📝 进程配置")
        
        num_processes = st.slider(
            "进程数量",
            min_value=2,
            max_value=6,
            value=3,
            help="要创建的进程数量"
        )
        
        # 为每个进程配置指令数
        process_configs = []
        for i in range(num_processes):
            with st.expander(f"进程 P{i+1} 配置"):
                instructions = st.number_input(
                    f"P{i+1} 总指令数",
                    min_value=50,
                    max_value=500,
                    value=100 + i * 50,
                    step=10,
                    key=f"process_{i}_instructions"
                )
                priority = st.number_input(
                    f"P{i+1} 优先级",
                    min_value=0,
                    max_value=10,
                    value=0,
                    key=f"process_{i}_priority"
                )
                process_configs.append({
                    'name': f'P{i+1}',
                    'instructions': instructions,
                    'priority': priority
                })
        
        st.markdown("---")
        
        # 仿真控制
        st.subheader("🚀 仿真控制")
        
        if st.button("🔧 配置系统", use_container_width=True):
            # 重新创建仿真器
            st.session_state.simulator = IntegratedSimulator()
            
            # 配置系统参数
            st.session_state.simulator.configure_system(
                time_quantum, instructions_per_time_unit, memory_size, algorithm
            )
            
            # 添加进程
            for config in process_configs:
                st.session_state.simulator.add_process(
                    config['name'], config['instructions'], config['priority']
                )
            
            st.success("系统配置完成！")
        
        if st.button("▶️ 开始仿真", use_container_width=True):
            if st.session_state.simulator.processes:
                with st.spinner("正在运行仿真..."):
                    st.session_state.simulation_report = st.session_state.simulator.run_simulation()
                st.success("仿真完成！")
                st.rerun()
            else:
                st.error("请先配置系统！")
        
        if st.button("🔄 重置仿真", use_container_width=True):
            st.session_state.simulator = IntegratedSimulator()
            st.session_state.simulation_report = None
            st.info("仿真已重置")
            st.rerun()
    
    # 主显示区域
    if st.session_state.simulation_report:
        report = st.session_state.simulation_report
        
        # 标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 仿真概览", "📈 甘特图", "💾 内存分析", "📋 详细日志", "📈 性能分析"
        ])
        
        with tab1:
            st.subheader("仿真结果概览")
            
            # 关键指标
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总执行时间", f"{report['total_time']} 时间片")
            with col2:
                st.metric("总指令数", f"{report['total_instructions']} 条")
            with col3:
                st.metric("总缺页数", f"{report['total_page_faults']} 次")
            with col4:
                st.metric("缺页率", f"{report['page_fault_rate']:.3f}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("系统吞吐量", f"{report['throughput']:.3f} 进程/时间片")
            with col2:
                avg_turnaround = sum(p['turnaround_time'] for p in report['processes']) / len(report['processes'])
                st.metric("平均周转时间", f"{avg_turnaround:.2f} 时间片")
            
            # 进程完成情况
            st.subheader("进程完成情况")
            
            process_df = pd.DataFrame(report['processes'])
            process_df['完成时间'] = process_df['completion_time']
            process_df['周转时间'] = process_df['turnaround_time']
            process_df['总指令数'] = process_df['total_instructions']
            
            st.dataframe(
                process_df[['name', '总指令数', '完成时间', '周转时间']].rename(columns={'name': '进程名'}),
                use_container_width=True,
                hide_index=True
            )
        
        with tab2:
            st.subheader("进程调度甘特图")
            
            gantt_fig = create_gantt_chart(report['gantt_data'])
            if gantt_fig:
                st.plotly_chart(gantt_fig, use_container_width=True)
            
            # 甘特图数据表
            st.subheader("调度详情")
            gantt_df = pd.DataFrame(report['gantt_data'])
            if not gantt_df.empty:
                display_df = gantt_df.copy()
                display_df['开始时间'] = display_df['Start']
                display_df['结束时间'] = display_df['Finish']
                display_df['持续时间'] = display_df['Duration']
                display_df['执行指令'] = display_df['Instructions']
                display_df['缺页次数'] = display_df['Page_Faults']
                
                st.dataframe(
                    display_df[['Process', '开始时间', '结束时间', '持续时间', '执行指令', '缺页次数']].rename(columns={'Process': '进程'}),
                    use_container_width=True,
                    hide_index=True
                )
        
        with tab3:
            st.subheader("内存管理分析")
            
            # 内存缺页统计图
            memory_fault_fig = create_memory_fault_chart(report['memory_stats'])
            if memory_fault_fig:
                st.plotly_chart(memory_fault_fig, use_container_width=True)
            
            # 内存统计表
            if report['memory_stats']:
                st.subheader("内存访问统计")
                memory_df = pd.DataFrame(report['memory_stats'])
                
                # 按进程统计
                process_memory_stats = memory_df.groupby('process').agg({
                    'page_faults': 'sum',
                    'memory_usage': 'mean'
                }).round(2)
                
                process_memory_stats['平均内存使用'] = process_memory_stats['memory_usage']
                process_memory_stats['总缺页数'] = process_memory_stats['page_faults']
                
                st.dataframe(
                    process_memory_stats[['总缺页数', '平均内存使用']],
                    use_container_width=True
                )
        
        with tab4:
            st.subheader("详细执行日志")
            
            if report['execution_log']:
                log_df = pd.DataFrame(report['execution_log'])
                
                # 格式化显示
                display_log = log_df.copy()
                display_log['时间'] = display_log['time']
                display_log['进程'] = display_log['process']
                display_log['执行指令数'] = display_log['instructions_executed']
                display_log['缺页次数'] = display_log['page_faults']
                display_log['完成进度'] = display_log['progress'].round(1).astype(str) + '%'
                display_log['状态'] = display_log['status'].map({
                    'running': '运行中',
                    'completed': '已完成'
                })
                
                st.dataframe(
                    display_log[['时间', '进程', '执行指令数', '缺页次数', '完成进度', '状态']],
                    use_container_width=True,
                    hide_index=True
                )
        
        with tab5:
            st.subheader("系统性能分析")
            
            performance_fig = create_system_performance_chart(report)
            if performance_fig:
                st.plotly_chart(performance_fig, use_container_width=True)
            
            # 性能分析结论
            st.subheader("性能分析结论")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**调度效率分析**")
                avg_turnaround = sum(p['turnaround_time'] for p in report['processes']) / len(report['processes'])
                if avg_turnaround < report['total_time'] * 0.8:
                    st.success("✅ 调度效率良好，平均周转时间较短")
                else:
                    st.warning("⚠️ 调度效率有待提升，考虑优化时间片大小")
                
                st.write(f"- 平均周转时间: {avg_turnaround:.2f} 时间片")
                st.write(f"- 时间片利用率: {(report['total_instructions'] / (report['total_time'] * report['total_instructions'] / len(report['processes']))):.3f}")
            
            with col2:
                st.write("**内存管理分析**")
                if report['page_fault_rate'] < 0.3:
                    st.success("✅ 内存管理效率良好，缺页率较低")
                elif report['page_fault_rate'] < 0.5:
                    st.warning("⚠️ 内存管理一般，可考虑增加内存容量")
                else:
                    st.error("❌ 缺页率过高，建议增加内存或优化算法")
                
                st.write(f"- 缺页率: {report['page_fault_rate']:.3f}")
                st.write(f"- 内存算法: {st.session_state.simulator.algorithm}")
            
            # 优化建议
            st.subheader("🎯 系统优化建议")
            
            suggestions = []
            
            if report['page_fault_rate'] > 0.4:
                suggestions.append("📈 考虑增加内存容量或使用更高效的页面置换算法")
            
            if avg_turnaround > report['total_time'] * 0.7:
                suggestions.append("⏱️ 考虑调整时间片大小，可能需要更短的时间片")
            
            if report['throughput'] < 0.3:
                suggestions.append("🚀 系统吞吐量较低，考虑优化进程调度策略")
            
            instructions_variance = pd.DataFrame(report['processes'])['total_instructions'].std()
            if instructions_variance > 50:
                suggestions.append("⚖️ 进程指令数差异较大，考虑使用优先级调度")
            
            if not suggestions:
                st.success("🎉 系统性能表现良好，无明显优化需求！")
            else:
                for suggestion in suggestions:
                    st.info(suggestion)
    
    else:
        # 欢迎页面
        st.info("👈 请在左侧配置系统参数并开始仿真")
        
        st.markdown("""
        ### 🌟 增强版融合平台特色功能
        
        #### 🎯 仿真测试功能
        - **指令级仿真**: 每个进程执行真实的指令序列
        - **时间片配置**: 可调整时间片大小和每时间片指令数
        - **内存集成**: 指令执行与内存访问紧密结合
        - **实时统计**: 全程记录执行过程和性能指标
        
        #### 📊 甘特图可视化
        - **时间轴展示**: 直观显示进程调度时间线
        - **详细信息**: 每个时间片的指令数和缺页数
        - **交互式图表**: 支持缩放和详情查看
        - **多维数据**: 集成调度和内存信息
        
        #### 🔧 系统配置
        - **灵活参数**: 时间片、指令数、内存大小全可调
        - **多种算法**: 支持FIFO、LRU、OPT页面置换
        - **进程定制**: 每个进程可设置不同指令数和优先级
        - **一键仿真**: 配置完成后一键运行完整仿真
        
        #### 📈 深度分析
        - **性能指标**: 吞吐量、周转时间、缺页率等
        - **趋势分析**: 内存使用趋势和缺页变化
        - **优化建议**: 基于仿真结果提供系统优化建议
        - **对比分析**: 支持不同配置下的性能对比
        
        ### 🚀 开始使用
        1. 在左侧配置系统参数（时间片、内存等）
        2. 设置进程信息（指令数、优先级）
        3. 点击"配置系统"完成初始化
        4. 点击"开始仿真"运行完整仿真
        5. 在不同标签页查看详细结果和分析
        """)

if __name__ == "__main__":
    main() 