import random
import time
from typing import List, Dict, Tuple, Optional
from collections import deque

class InstructionGenerator:
    """指令序列生成器"""
    
    def __init__(self, total_instructions: int = 320):
        self.total_instructions = total_instructions
        self.instructions = []
    
    def generate_instructions(self) -> List[int]:
        """生成指令序列"""
        instructions = []
        i = 0
        
        while i < self.total_instructions:
            # 随机产生起点m
            m = random.randint(0, self.total_instructions - 1)
            instructions.append(m)
            i += 1
            
            if i >= self.total_instructions:
                break
            
            # 顺序执行一条指令 (m+1)
            if m + 1 < self.total_instructions:
                instructions.append(m + 1)
                i += 1
            
            if i >= self.total_instructions:
                break
            
            # 在[0, m+1]中随机选取指令
            m1 = random.randint(0, m + 1)
            instructions.append(m1)
            i += 1
            
            if i >= self.total_instructions:
                break
            
            # 顺序执行一条指令 (m1+1)
            if m1 + 1 < self.total_instructions:
                instructions.append(m1 + 1)
                i += 1
            
            if i >= self.total_instructions:
                break
            
            # 在[m1+2, 319]中随机选取指令
            if m1 + 2 < self.total_instructions:
                m2 = random.randint(m1 + 2, self.total_instructions - 1)
                instructions.append(m2)
                i += 1
        
        # 确保正好320条指令
        self.instructions = instructions[:self.total_instructions]
        return self.instructions
    
    def instructions_to_pages(self, instructions: List[int]) -> List[int]:
        """将指令序列转换为页地址流"""
        pages = []
        for instruction in instructions:
            # 每页10条指令，指令地址/10就是页号
            page_num = instruction // 10
            pages.append(page_num)
        return pages

class PageReplacementAlgorithm:
    """页面置换算法基类"""
    
    def __init__(self, memory_size: int):
        self.memory_size = memory_size
        self.memory = []  # 内存中的页面
        self.page_faults = 0  # 缺页次数
        self.access_log = []  # 访问日志
        
    def access_page(self, page: int) -> bool:
        """访问页面，返回是否发生缺页"""
        raise NotImplementedError
    
    def get_hit_rate(self, total_accesses: int) -> float:
        """计算命中率"""
        return 1 - (self.page_faults / total_accesses)
    
    def reset(self):
        """重置状态"""
        self.memory = []
        self.page_faults = 0
        self.access_log = []

class FIFOAlgorithm(PageReplacementAlgorithm):
    """先进先出(FIFO)页面置换算法"""
    
    def __init__(self, memory_size: int):
        super().__init__(memory_size)
        self.queue = deque()
    
    def access_page(self, page: int) -> bool:
        """访问页面"""
        is_fault = False
        memory_before = self.memory.copy()
        
        if page in self.memory:
            # 页面命中
            action = "命中"
        else:
            # 页面缺失
            is_fault = True
            self.page_faults += 1
            action = "缺页"
            
            if len(self.memory) < self.memory_size:
                # 内存未满，直接添加
                self.memory.append(page)
                self.queue.append(page)
            else:
                # 内存已满，替换最早进入的页面
                old_page = self.queue.popleft()
                self.memory.remove(old_page)
                self.memory.append(page)
                self.queue.append(page)
                action = f"缺页(替换{old_page})"
        
        # 记录访问日志
        log_entry = {
            'page': page,
            'action': action,
            'memory_before': memory_before,
            'memory_after': self.memory.copy(),
            'is_fault': is_fault
        }
        self.access_log.append(log_entry)
        
        return is_fault
    
    def reset(self):
        super().reset()
        self.queue = deque()

class LRUAlgorithm(PageReplacementAlgorithm):
    """最近最少使用(LRU)页面置换算法"""
    
    def __init__(self, memory_size: int):
        super().__init__(memory_size)
        self.access_time = {}  # 记录每个页面的最后访问时间
        self.time_counter = 0
    
    def access_page(self, page: int) -> bool:
        """访问页面"""
        is_fault = False
        memory_before = self.memory.copy()
        self.time_counter += 1
        
        if page in self.memory:
            # 页面命中，更新访问时间
            self.access_time[page] = self.time_counter
            action = "命中"
        else:
            # 页面缺失
            is_fault = True
            self.page_faults += 1
            action = "缺页"
            
            if len(self.memory) < self.memory_size:
                # 内存未满，直接添加
                self.memory.append(page)
                self.access_time[page] = self.time_counter
            else:
                # 内存已满，替换最近最少使用的页面
                lru_page = min(self.memory, key=lambda p: self.access_time[p])
                self.memory.remove(lru_page)
                del self.access_time[lru_page]
                self.memory.append(page)
                self.access_time[page] = self.time_counter
                action = f"缺页(替换{lru_page})"
        
        # 记录访问日志
        log_entry = {
            'page': page,
            'action': action,
            'memory_before': memory_before,
            'memory_after': self.memory.copy(),
            'is_fault': is_fault
        }
        self.access_log.append(log_entry)
        
        return is_fault
    
    def reset(self):
        super().reset()
        self.access_time = {}
        self.time_counter = 0

class OptimalAlgorithm(PageReplacementAlgorithm):
    """最佳淘汰算法(OPT)"""
    
    def __init__(self, memory_size: int):
        super().__init__(memory_size)
        self.future_pages = []  # 未来的页面访问序列
        self.current_index = 0
    
    def set_future_pages(self, pages: List[int]):
        """设置未来的页面访问序列"""
        self.future_pages = pages
        self.current_index = 0
    
    def access_page(self, page: int) -> bool:
        """访问页面"""
        is_fault = False
        memory_before = self.memory.copy()
        
        if page in self.memory:
            # 页面命中
            action = "命中"
        else:
            # 页面缺失
            is_fault = True
            self.page_faults += 1
            action = "缺页"
            
            if len(self.memory) < self.memory_size:
                # 内存未满，直接添加
                self.memory.append(page)
            else:
                # 内存已满，替换将来不再使用或最晚使用的页面
                victim_page = self._find_optimal_victim()
                self.memory.remove(victim_page)
                self.memory.append(page)
                action = f"缺页(替换{victim_page})"
        
        # 记录访问日志
        log_entry = {
            'page': page,
            'action': action,
            'memory_before': memory_before,
            'memory_after': self.memory.copy(),
            'is_fault': is_fault
        }
        self.access_log.append(log_entry)
        
        self.current_index += 1
        return is_fault
    
    def _find_optimal_victim(self) -> int:
        """找到最佳的被替换页面"""
        future_use = {}
        
        # 查看每个在内存中的页面在未来的使用情况
        for mem_page in self.memory:
            next_use = float('inf')  # 如果未来不再使用，设为无穷大
            for i in range(self.current_index + 1, len(self.future_pages)):
                if self.future_pages[i] == mem_page:
                    next_use = i
                    break
            future_use[mem_page] = next_use
        
        # 选择未来最晚使用的页面进行替换
        victim = max(future_use.keys(), key=lambda p: future_use[p])
        return victim
    
    def reset(self):
        super().reset()
        self.current_index = 0

class LFRAlgorithm(PageReplacementAlgorithm):
    """最少访问页面算法(LFR - Least Frequently Recently used)"""
    
    def __init__(self, memory_size: int):
        super().__init__(memory_size)
        self.access_count = {}  # 记录每个页面的访问次数
        self.access_time = {}   # 记录每个页面的最后访问时间
        self.time_counter = 0
    
    def access_page(self, page: int) -> bool:
        """访问页面"""
        is_fault = False
        memory_before = self.memory.copy()
        self.time_counter += 1
        
        if page in self.memory:
            # 页面命中，更新访问次数和时间
            self.access_count[page] = self.access_count.get(page, 0) + 1
            self.access_time[page] = self.time_counter
            action = "命中"
        else:
            # 页面缺失
            is_fault = True
            self.page_faults += 1
            action = "缺页"
            
            if len(self.memory) < self.memory_size:
                # 内存未满，直接添加
                self.memory.append(page)
                self.access_count[page] = 1
                self.access_time[page] = self.time_counter
            else:
                # 内存已满，替换访问次数最少的页面，如果次数相同则替换最早访问的
                lfr_page = min(self.memory, key=lambda p: (
                    self.access_count.get(p, 0), 
                    -self.access_time.get(p, 0)
                ))
                self.memory.remove(lfr_page)
                del self.access_count[lfr_page]
                del self.access_time[lfr_page]
                self.memory.append(page)
                self.access_count[page] = 1
                self.access_time[page] = self.time_counter
                action = f"缺页(替换{lfr_page})"
        
        # 记录访问日志
        log_entry = {
            'page': page,
            'action': action,
            'memory_before': memory_before,
            'memory_after': self.memory.copy(),
            'is_fault': is_fault
        }
        self.access_log.append(log_entry)
        
        return is_fault
    
    def reset(self):
        super().reset()
        self.access_count = {}
        self.access_time = {}
        self.time_counter = 0

class MemoryManager:
    """内存管理器"""
    
    def __init__(self):
        self.algorithms = {
            'FIFO': FIFOAlgorithm,
            'LRU': LRUAlgorithm,
            'OPT': OptimalAlgorithm,
            'LFR': LFRAlgorithm
        }
        self.instruction_generator = InstructionGenerator()
    
    def simulate(self, algorithm_name: str, memory_size: int, instructions: List[int] = None) -> Dict:
        """模拟页面置换算法"""
        if algorithm_name not in self.algorithms:
            raise ValueError(f"不支持的算法: {algorithm_name}")
        
        # 生成指令序列（如果没有提供）
        if instructions is None:
            instructions = self.instruction_generator.generate_instructions()
        
        # 转换为页地址流
        pages = self.instruction_generator.instructions_to_pages(instructions)
        
        # 创建算法实例
        algorithm = self.algorithms[algorithm_name](memory_size)
        
        # 对于最佳算法，需要提供未来的页面序列
        if algorithm_name == 'OPT':
            algorithm.set_future_pages(pages)
        
        # 模拟页面访问
        for page in pages:
            algorithm.access_page(page)
        
        # 计算统计信息
        hit_rate = algorithm.get_hit_rate(len(pages))
        
        result = {
            'algorithm': algorithm_name,
            'memory_size': memory_size,
            'total_accesses': len(pages),
            'page_faults': algorithm.page_faults,
            'hit_rate': hit_rate,
            'pages': pages,
            'access_log': algorithm.access_log,
            'instructions': instructions
        }
        
        return result
    
    def compare_algorithms(self, memory_sizes: List[int], instructions: List[int] = None) -> Dict:
        """比较不同算法在不同内存大小下的性能"""
        if instructions is None:
            instructions = self.instruction_generator.generate_instructions()
        
        results = {}
        
        for memory_size in memory_sizes:
            results[memory_size] = {}
            for algorithm_name in self.algorithms.keys():
                result = self.simulate(algorithm_name, memory_size, instructions)
                results[memory_size][algorithm_name] = {
                    'page_faults': result['page_faults'],
                    'hit_rate': result['hit_rate']
                }
        
        return {
            'comparison': results,
            'instructions': instructions,
            'pages': self.instruction_generator.instructions_to_pages(instructions)
        } 