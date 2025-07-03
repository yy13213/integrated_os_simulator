import random

class PCB:
    """进程控制块"""
    def __init__(self, name, require_time):
        self.name = name                    # 进程名
        self.next = None                    # 指针，指向下一个进程
        self.require_time = require_time    # 要求运行时间
        self.run_time = 0                   # 已运行时间
        self.status = 'R'                   # 状态：R-就绪，E-结束
    
    def __str__(self):
        return f"进程名: {self.name}, 要求运行时间: {self.require_time}, 已运行时间: {self.run_time}, 状态: {self.status}"

class ProcessScheduler:
    """进程调度器"""
    def __init__(self):
        self.current = None    # 标志单元，指向当前要运行的进程
        self.process_count = 0 # 就绪状态进程数量
    
    def create_processes(self):
        """创建5个进程并设置随机的要求运行时间"""
        print("=== 创建进程 ===")
        processes = []
        
        # 为五个进程随机确定要求运行时间
        for i in range(1, 6):
            require_time = random.randint(1, 8)  # 随机生成1-8的运行时间
            process = PCB(f"Q{i}", require_time)
            processes.append(process)
            print(f"进程 Q{i} 要求运行时间: {require_time}")
        
        # 构建循环队列
        for i in range(5):
            processes[i].next = processes[(i + 1) % 5]
        
        self.current = processes[0]  # 标志单元指向第一个进程
        self.process_count = 5
        
        print("\n=== 初始进程控制块状态 ===")
        self.display_all_processes()
        return processes[0]
    
    def display_all_processes(self):
        """显示所有进程的状态"""
        if self.current is None:
            print("没有进程")
            return
        
        start = self.current
        processes = []
        
        # 收集所有进程信息
        temp = start
        while True:
            processes.append(temp)
            temp = temp.next
            if temp == start:
                break
        
        # 按进程名排序显示
        processes.sort(key=lambda x: x.name)
        
        print(f"{'进程名':<8} {'要求运行时间':<12} {'已运行时间':<12} {'状态':<6}")
        print("-" * 50)
        for process in processes:
            print(f"{process.name:<8} {process.require_time:<12} {process.run_time:<12} {process.status:<6}")
        print()
    
    def run_process(self):
        """运行当前进程一个时间片"""
        if self.current is None or self.process_count == 0:
            return False
        
        current_process = self.current
        print(f"选中进程: {current_process.name}")
        
        # 模拟进程运行一个时间片
        current_process.run_time += 1
        
        # 检查进程是否完成
        if current_process.run_time >= current_process.require_time:
            # 进程完成，修改状态为结束
            current_process.status = 'E'
            print(f"进程 {current_process.name} 运行完成！")
            
            # 从循环队列中移除该进程
            if self.process_count == 1:
                # 最后一个进程
                self.current = None
                self.process_count = 0
            else:
                # 找到前一个进程
                prev = current_process
                while prev.next != current_process:
                    prev = prev.next
                
                # 将前一个进程的指针指向当前进程的下一个进程
                prev.next = current_process.next
                self.current = current_process.next
                self.process_count -= 1
        else:
            # 进程未完成，切换到下一个进程
            self.current = current_process.next
        
        return True
    
    def schedule(self):
        """执行调度"""
        print("=== 开始时间片轮转调度 ===\n")
        
        round_count = 1
        while self.process_count > 0:
            print(f"--- 第 {round_count} 轮调度 ---")
            
            if not self.run_process():
                break
            
            print("运行后各进程状态:")
            self.display_all_processes()
            
            round_count += 1
        
        print("=== 所有进程调度完成 ===")

def main():
    """主函数"""
    print("操作系统实验 - 时间片轮转法进程调度")
    print("=" * 50)
    
    scheduler = ProcessScheduler()
    
    # 创建进程
    scheduler.create_processes()
    
    input("\n按回车键开始调度...")
    
    # 执行调度
    scheduler.schedule()
    
    print("\n实验结束！")

if __name__ == "__main__":
    main() 