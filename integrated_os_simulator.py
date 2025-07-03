import random
import time
from typing import List, Dict, Tuple, Optional
from collections import deque
from dataclasses import dataclass
from enum import Enum

class ProcessState(Enum):
    """进程状态枚举"""
    READY = "R"  # 就绪
    RUNNING = "运行"  # 运行
    BLOCKED = "阻塞"  # 阻塞
    TERMINATED = "E"  # 结束

@dataclass
class PCB:
    """进程控制块"""
    name: str
    pid: int
    required_time: int  # 要求运行时间
    executed_time: int = 0  # 已运行时间
    state: ProcessState = ProcessState.READY
    next_process: Optional['PCB'] = None
    
    # 新增：指令相关
    instruction_sequence: List[int] = None  # 进程的指令序列
    current_instruction_index: int = 0  # 当前指令索引
    total_instructions: int = 0  # 总指令数
    
    # 新增：内存相关
    allocated_pages: set = None  # 分配的页面集合
    page_faults: int = 0  # 缺页次数
    
    def __post_init__(self):
        if self.allocated_pages is None:
            self.allocated_pages = set()
        if self.instruction_sequence is None:
            self.instruction_sequence = []

class InstructionGenerator:
    """指令序列生成器"""
    
    @staticmethod
    def generate_process_instructions(process_id: int, total_instructions: int = 320) -> List[int]:
        """为特定进程生成指令序列"""
        instructions = []
        i = 0
        
        # 为不同进程设置不同的地址范围，模拟进程隔离
        base_address = process_id * 100
        max_address = base_address + total_instructions - 1
        
        while i < total_instructions:
            # 随机产生起点m（在进程地址空间内）
            m = random.randint(base_address, max_address)
            instructions.append(m)
            i += 1
            
            if i >= total_instructions:
                break
            
            # 顺序执行一条指令 (m+1)
            if m + 1 <= max_address:
                instructions.append(m + 1)
                i += 1
            
            if i >= total_instructions:
                break
            
            # 在[base_address, m+1]中随机选取指令
            m1 = random.randint(base_address, min(m + 1, max_address))
            instructions.append(m1)
            i += 1
            
            if i >= total_instructions:
                break
            
            # 顺序执行一条指令 (m1+1)
            if m1 + 1 <= max_address:
                instructions.append(m1 + 1)
                i += 1
            
            if i >= total_instructions:
                break
            
            # 在[m1+2, max_address]中随机选取指令
            if m1 + 2 <= max_address:
                m2 = random.randint(m1 + 2, max_address)
                instructions.append(m2)
                i += 1
        
        return instructions[:total_instructions]
    
    @staticmethod
    def instructions_to_pages(instructions: List[int], page_size: int = 10) -> List[int]:
        """将指令序列转换为页地址流"""
        pages = []
        for instruction in instructions:
            page_num = instruction // page_size
            pages.append(page_num)
        return pages

class MemoryManager:
    """内存管理器"""
    
    def __init__(self, total_memory_pages: int = 32):
        self.total_memory_pages = total_memory_pages
        self.allocated_pages = {}  # {process_id: set of pages}
        self.page_replacement_algorithm = "LRU"
        self.access_history = {}  # {process_id: [(page, time), ...]}
        self.time_counter = 0
    
    def allocate_initial_pages(self, process_id: int, required_pages: int) -> bool:
        """为进程分配初始页面"""
        if len(self.get_all_allocated_pages()) + required_pages > self.total_memory_pages:
            return False
        
        if process_id not in self.allocated_pages:
            self.allocated_pages[process_id] = set()
        
        # 分配连续的页面
        start_page = len(self.get_all_allocated_pages())
        for i in range(required_pages):
            self.allocated_pages[process_id].add(start_page + i)
        
        return True
    
    def get_all_allocated_pages(self) -> set:
        """获取所有已分配的页面"""
        all_pages = set()
        for pages in self.allocated_pages.values():
            all_pages.update(pages)
        return all_pages
    
    def access_page(self, process_id: int, page: int, process_memory_limit: int) -> bool:
        """访问页面，返回是否发生缺页"""
        self.time_counter += 1
        
        if process_id not in self.allocated_pages:
            self.allocated_pages[process_id] = set()
        
        if process_id not in self.access_history:
            self.access_history[process_id] = []
        
        # 检查页面是否在内存中
        if page in self.allocated_pages[process_id]:
            # 页面命中，更新访问历史
            self.access_history[process_id].append((page, self.time_counter))
            return False  # 无缺页
        else:
            # 页面缺失
            current_process_pages = len(self.allocated_pages[process_id])
            total_system_pages = len(self.get_all_allocated_pages())
            
            # 检查是否有空间分配新页面
            can_allocate_new = (current_process_pages < process_memory_limit and 
                              total_system_pages < self.total_memory_pages)
            
            if can_allocate_new:
                # 还有空闲内存，直接分配
                self.allocated_pages[process_id].add(page)
            else:
                # 需要页面置换
                if current_process_pages > 0:
                    victim_page = self._select_victim_page(process_id)
                    self.allocated_pages[process_id].remove(victim_page)
                self.allocated_pages[process_id].add(page)
            
            self.access_history[process_id].append((page, self.time_counter))
            return True  # 发生缺页
    
    def _select_victim_page(self, process_id: int) -> int:
        """选择被置换的页面（LRU算法）"""
        if process_id not in self.access_history or not self.access_history[process_id]:
            # 如果没有访问历史，随机选择
            return list(self.allocated_pages[process_id])[0]
        
        # LRU算法：选择最长时间未被访问的页面
        page_last_access = {}
        for page, access_time in self.access_history[process_id]:
            page_last_access[page] = access_time
        
        # 在当前分配的页面中找到最久未访问的
        lru_page = None
        lru_time = float('inf')
        for page in self.allocated_pages[process_id]:
            last_access = page_last_access.get(page, 0)
            if last_access < lru_time:
                lru_time = last_access
                lru_page = page
        
        return lru_page if lru_page is not None else list(self.allocated_pages[process_id])[0]
    
    def deallocate_process_pages(self, process_id: int):
        """释放进程的所有页面"""
        if process_id in self.allocated_pages:
            del self.allocated_pages[process_id]
        if process_id in self.access_history:
            del self.access_history[process_id]

class IntegratedScheduler:
    """融合的进程调度器"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.processes: List[PCB] = []
        self.current_process_index = 0
        self.time_quantum = 2  # 时间片大小
        self.instructions_per_time_unit = 5  # 每个时间单位执行的指令数
        self.current_time = 0
        self.memory_manager = memory_manager
        self.execution_log = []  # 执行日志
        
    def add_process(self, name: str, required_time: int, memory_limit: int = 8) -> PCB:
        """添加进程"""
        process = PCB(
            name=name,
            pid=len(self.processes),
            required_time=required_time,
            total_instructions=320  # 固定为320条指令
        )
        
        # 为进程生成指令序列（固定320条）
        process.instruction_sequence = InstructionGenerator.generate_process_instructions(
            process.pid, 320
        )
        
        # 为进程分配初始内存
        self.memory_manager.allocate_initial_pages(process.pid, min(memory_limit, 4))
        
        self.processes.append(process)
        
        # 设置循环链表
        if len(self.processes) > 1:
            self.processes[-2].next_process = process
            process.next_process = self.processes[0]
        else:
            process.next_process = process
        
        return process
    
    def execute_instructions(self, process: PCB, instruction_count: int) -> Dict:
        """执行指定数量的指令"""
        execution_info = {
            'executed_instructions': 0,
            'page_faults': 0,
            'accessed_pages': [],
            'instruction_addresses': []
        }
        
        for _ in range(instruction_count):
            if process.current_instruction_index >= len(process.instruction_sequence):
                break
            
            # 获取当前指令地址
            instruction_addr = process.instruction_sequence[process.current_instruction_index]
            execution_info['instruction_addresses'].append(instruction_addr)
            
            # 转换为页号
            page_num = instruction_addr // 10
            execution_info['accessed_pages'].append(page_num)
            
            # 检查是否需要页面置换
            is_fault = self.memory_manager.access_page(
                process.pid, 
                page_num, 
                process_memory_limit=8
            )
            
            if is_fault:
                execution_info['page_faults'] += 1
                process.page_faults += 1
            
            process.current_instruction_index += 1
            execution_info['executed_instructions'] += 1
        
        return execution_info
    
    def schedule_next_process(self) -> Optional[PCB]:
        """选择下一个要执行的进程"""
        if not self.processes:
            return None
        
        # 查找下一个就绪状态的进程
        start_index = self.current_process_index
        attempts = 0
        
        while attempts < len(self.processes):
            current_process = self.processes[self.current_process_index]
            
            if current_process.state == ProcessState.READY:
                return current_process
            
            self.current_process_index = (self.current_process_index + 1) % len(self.processes)
            attempts += 1
        
        return None
    
    def run_time_slice(self) -> Dict:
        """运行一个时间片"""
        current_process = self.schedule_next_process()
        
        if not current_process:
            return {'status': 'no_ready_process'}
        
        # 设置进程为运行状态
        old_state = current_process.state
        current_process.state = ProcessState.RUNNING
        
        # 在一个时间片内运行time_quantum个时间单位
        total_execution_info = {
            'executed_instructions': 0,
            'page_faults': 0,
            'accessed_pages': [],
            'instruction_addresses': []
        }
        
        # 运行time_quantum个时间单位
        for _ in range(self.time_quantum):
            # 执行一个时间单位的指令
            execution_info = self.execute_instructions(
                current_process, 
                self.instructions_per_time_unit
            )
            
            # 累积执行信息
            total_execution_info['executed_instructions'] += execution_info['executed_instructions']
            total_execution_info['page_faults'] += execution_info['page_faults']
            total_execution_info['accessed_pages'].extend(execution_info['accessed_pages'])
            total_execution_info['instruction_addresses'].extend(execution_info['instruction_addresses'])
            
            # 更新进程执行时间
            current_process.executed_time += 1
            
            # 检查进程是否在时间片内完成
            instructions_completed = current_process.current_instruction_index >= len(current_process.instruction_sequence)
            time_completed = current_process.executed_time >= current_process.required_time
            
            if instructions_completed or time_completed:
                break
        
        # 检查进程是否完成（时间到达或指令执行完毕）
        instructions_completed = current_process.current_instruction_index >= len(current_process.instruction_sequence)
        time_completed = current_process.executed_time >= current_process.required_time
        
        if instructions_completed or time_completed:
            current_process.state = ProcessState.TERMINATED
            # 释放进程内存
            self.memory_manager.deallocate_process_pages(current_process.pid)
        else:
            current_process.state = ProcessState.READY
        
        # 记录执行日志
        log_entry = {
            'time': self.current_time,
            'process': current_process.name,
            'pid': current_process.pid,
            'executed_time': current_process.executed_time,
            'required_time': current_process.required_time,
            'state': current_process.state.value,
            'execution_info': total_execution_info,
            'memory_pages': list(self.memory_manager.allocated_pages.get(current_process.pid, set())),
            'time_quantum_used': self.time_quantum
        }
        
        self.execution_log.append(log_entry)
        
        # 移动到下一个进程
        self.current_process_index = (self.current_process_index + 1) % len(self.processes)
        self.current_time += 1
        
        return log_entry
    
    def run_simulation(self) -> List[Dict]:
        """运行完整的模拟"""
        while any(p.state != ProcessState.TERMINATED for p in self.processes):
            result = self.run_time_slice()
            if result.get('status') == 'no_ready_process':
                break
        
        return self.execution_log
    
    def get_process_statistics(self) -> Dict:
        """获取进程统计信息"""
        stats = {}
        for process in self.processes:
            stats[process.name] = {
                'pid': process.pid,
                'required_time': process.required_time,
                'executed_time': process.executed_time,
                'total_instructions': process.total_instructions,
                'executed_instructions': process.current_instruction_index,
                'page_faults': process.page_faults,
                'state': process.state.value,
                'completion_rate': process.executed_time / process.required_time if process.required_time > 0 else 0
            }
        return stats
    
    def get_memory_statistics(self) -> Dict:
        """获取内存统计信息"""
        # 正确计算已分配页面数，确保不超过物理内存
        active_processes = {pid: pages for pid, pages in self.memory_manager.allocated_pages.items() if pages}
        total_allocated = sum(len(pages) for pages in active_processes.values())
        total_capacity = self.memory_manager.total_memory_pages
        
        # 确保已分配不超过总容量
        total_allocated = min(total_allocated, total_capacity)
        
        return {
            'total_capacity': total_capacity,
            'total_allocated': total_allocated,
            'utilization_rate': total_allocated / total_capacity if total_capacity > 0 else 0,
            'allocated_by_process': dict(active_processes),
            'free_pages': max(0, total_capacity - total_allocated)
        }

# 示例使用
if __name__ == "__main__":
    # 创建内存管理器
    memory_mgr = MemoryManager(total_memory_pages=32)
    
    # 创建调度器
    scheduler = IntegratedScheduler(memory_mgr)
    
    # 添加进程
    scheduler.add_process("Q1", required_time=6)
    scheduler.add_process("Q2", required_time=4) 
    scheduler.add_process("Q3", required_time=8)
    scheduler.add_process("Q4", required_time=3)
    scheduler.add_process("Q5", required_time=5)
    
    # 运行模拟
    print("开始进程调度和内存管理综合模拟...")
    execution_log = scheduler.run_simulation()
    
    # 输出结果
    print("\n=== 执行日志 ===")
    for entry in execution_log:
        print(f"时间片 {entry['time']}: 进程 {entry['process']} "
              f"执行了 {entry['execution_info']['executed_instructions']} 条指令, "
              f"缺页 {entry['execution_info']['page_faults']} 次, "
              f"状态: {entry['state']}")
    
    # 输出统计信息
    print("\n=== 进程统计 ===")
    process_stats = scheduler.get_process_statistics()
    for name, stats in process_stats.items():
        print(f"{name}: 完成率 {stats['completion_rate']:.2%}, "
              f"缺页次数 {stats['page_faults']}, "
              f"状态 {stats['state']}")
    
    print("\n=== 内存统计 ===")
    memory_stats = scheduler.get_memory_statistics()
    print(f"内存利用率: {memory_stats['utilization_rate']:.2%}")
    print(f"总容量: {memory_stats['total_capacity']} 页")
    print(f"已分配: {memory_stats['total_allocated']} 页")
    print(f"空闲: {memory_stats['free_pages']} 页") 