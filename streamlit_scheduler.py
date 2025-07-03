import streamlit as st
import pandas as pd
import time
from typing import List, Dict, Optional

class PCB:
    """进程控制块"""
    def __init__(self, name: str, require_time: int):
        self.name = name
        self.next: Optional['PCB'] = None
        self.require_time = require_time
        self.run_time = 0
        self.status = 'R'  # R-就绪，E-结束
        self.last_run_round = 0  # 记录最后运行的轮次

class StreamlitScheduler:
    """Streamlit进程调度器"""
    
    def __init__(self):
        self.current: Optional[PCB] = None
        self.process_count = 0
        self.round_count = 0
        self.execution_log: List[Dict] = []
        self.is_running = False
        self.is_paused = False
        
    def create_processes(self, process_times: List[int]) -> None:
        """创建进程"""
        processes = []
        for i, require_time in enumerate(process_times, 1):
            if require_time > 0:  # 只创建运行时间大于0的进程
                process = PCB(f"Q{i}", require_time)
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
    
    def get_all_processes(self) -> List[PCB]:
        """获取所有进程"""
        if self.current is None:
            return []
        
        processes = []
        temp = self.current
        start_process = self.current
        
        # 找到队列中的第一个进程（按名称排序）
        while True:
            processes.append(temp)
            temp = temp.next
            if temp == start_process:
                break
        
        # 添加已完成的进程（从执行日志中获取）
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
        
        # 创建完整的进程列表（包括已完成的）
        all_processes = []
        for p in processes:
            all_processes.append(p)
        
        for name, data in completed_processes.items():
            completed_pcb = PCB(data['name'], data['require_time'])
            completed_pcb.run_time = data['run_time']
            completed_pcb.status = data['status']
            all_processes.append(completed_pcb)
        
        # 按进程名排序
        all_processes.sort(key=lambda x: x.name)
        return all_processes
    
    def run_one_step(self) -> bool:
        """执行一个调度步骤"""
        if self.current is None or self.process_count == 0:
            return False
        
        self.round_count += 1
        current_process = self.current
        
        # 记录调度前状态
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
        
        # 模拟进程运行一个时间片
        current_process.run_time += 1
        current_process.last_run_round = self.round_count
        
        # 检查进程是否完成
        if current_process.run_time >= current_process.require_time:
            current_process.status = 'E'
            log_entry['status'] = 'E'
            log_entry['action'] = '完成'
            
            # 从循环队列中移除该进程
            if self.process_count == 1:
                self.current = None
                self.process_count = 0
            else:
                # 找到前一个进程
                prev = current_process
                while prev.next != current_process:
                    prev = prev.next
                
                prev.next = current_process.next
                self.current = current_process.next
                self.process_count -= 1
        else:
            # 进程未完成，切换到下一个进程
            self.current = current_process.next
        
        self.execution_log.append(log_entry)
        return True
    
    def is_completed(self) -> bool:
        """检查所有进程是否完成"""
        return self.process_count == 0
    
    def reset(self) -> None:
        """重置调度器"""
        self.current = None
        self.process_count = 0
        self.round_count = 0
        self.execution_log = []
        self.is_running = False
        self.is_paused = False

def main():
    st.set_page_config(page_title="时间片轮转调度模拟器", page_icon="⚙️", layout="wide")
    
    st.title("⚙️ 时间片轮转调度模拟器")
    st.markdown("---")
    
    # 初始化会话状态
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = StreamlitScheduler()
    if 'auto_run' not in st.session_state:
        st.session_state.auto_run = False
    if 'step_delay' not in st.session_state:
        st.session_state.step_delay = 1.0
    
    scheduler = st.session_state.scheduler
    
    # 侧边栏控制面板
    with st.sidebar:
        st.header("🎛️ 控制面板")
        
        st.subheader("进程配置")
        process_times = []
        for i in range(1, 6):
            time_val = st.number_input(
                f"进程 Q{i} 运行时间", 
                min_value=0, 
                max_value=20, 
                value=0 if i > 2 else 5,  # 默认前两个进程有运行时间
                key=f"process_{i}"
            )
            process_times.append(time_val)
        
        st.subheader("调度控制")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 创建进程", use_container_width=True):
                scheduler.create_processes(process_times)
                st.session_state.auto_run = False
                st.rerun()
        
        with col2:
            if st.button("🔄 重置", use_container_width=True):
                scheduler.reset()
                st.session_state.auto_run = False
                st.rerun()
        
        # 单步执行和自动执行控制
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ 单步执行", use_container_width=True):
                if scheduler.process_count > 0:
                    scheduler.run_one_step()
                    st.rerun()
        
        with col2:
            if not st.session_state.auto_run:
                if st.button("🚀 自动执行", use_container_width=True):
                    if scheduler.process_count > 0:
                        st.session_state.auto_run = True
                        st.rerun()
            else:
                if st.button("⏸️ 暂停", use_container_width=True):
                    st.session_state.auto_run = False
                    st.rerun()
        
        # 自动执行速度控制
        st.session_state.step_delay = st.slider(
            "自动执行速度 (秒)", 
            min_value=0.1, 
            max_value=3.0, 
            value=st.session_state.step_delay,
            step=0.1
        )
    
    # 主显示区域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 进程状态表")
        
        if scheduler.process_count > 0 or scheduler.execution_log:
            processes = scheduler.get_all_processes()
            
            if processes:
                # 创建状态表
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
                    if scheduler.current and row['进程名'] == scheduler.current.name and row['状态'].endswith('就绪'):
                        return ['background-color: #ffeb3b; font-weight: bold'] * len(row)
                    elif row['状态'].endswith('完成'):
                        return ['background-color: #c8e6c9'] * len(row)
                    return [''] * len(row)
                
                styled_df = df.style.apply(highlight_current, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # 显示当前调度信息
                if scheduler.current:
                    st.info(f"🎯 当前调度: **{scheduler.current.name}** | 调度轮次: **{scheduler.round_count}**")
                elif scheduler.round_count > 0:
                    st.success("🎉 所有进程调度完成！")
            else:
                st.info("请在左侧配置进程运行时间并点击'创建进程'")
        else:
            st.info("请在左侧配置进程运行时间并点击'创建进程'")
    
    with col2:
        st.subheader("📈 统计信息")
        
        if scheduler.execution_log:
            total_rounds = scheduler.round_count
            completed_processes = len([log for log in scheduler.execution_log if log['action'] == '完成'])
            remaining_processes = scheduler.process_count
            
            st.metric("总调度轮次", total_rounds)
            st.metric("已完成进程", completed_processes)
            st.metric("剩余进程", remaining_processes)
            
            # 进程完成顺序
            if completed_processes > 0:
                st.subheader("🏁 完成顺序")
                completion_order = []
                for log in scheduler.execution_log:
                    if log['action'] == '完成':
                        completion_order.append(f"{log['process_name']} (第{log['round']}轮)")
                
                for i, process in enumerate(completion_order, 1):
                    st.write(f"{i}. {process}")
    
    # 执行日志
    if scheduler.execution_log:
        st.subheader("📝 执行日志")
        
        # 只显示最近的10条记录
        recent_logs = scheduler.execution_log[-10:]
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
    
    # 自动执行逻辑
    if st.session_state.auto_run and scheduler.process_count > 0:
        time.sleep(st.session_state.step_delay)
        scheduler.run_one_step()
        
        if scheduler.is_completed():
            st.session_state.auto_run = False
            st.success("🎉 自动调度完成！")
        
        st.rerun()
    
    # 底部说明
    st.markdown("---")
    st.markdown("""
    ### 📖 使用说明
    1. **配置进程**: 在左侧设置每个进程的运行时间（设为0表示不创建该进程）
    2. **创建进程**: 点击"创建进程"按钮初始化调度队列
    3. **执行调度**: 
       - 单步执行：逐步观察调度过程
       - 自动执行：连续执行直到所有进程完成
    4. **观察结果**: 查看进程状态表、统计信息和执行日志
    
    💡 **提示**: 黄色高亮显示当前正在运行的进程，绿色显示已完成的进程
    """)

if __name__ == "__main__":
    main() 