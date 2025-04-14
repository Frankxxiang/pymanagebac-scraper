import sqlite3
from datetime import datetime, timedelta
from src import pymanagebac as mb

def init_database():
    """初始化数据库并创建必要的表"""
    conn = sqlite3.connect('managebac.db')
    cursor = conn.cursor()
    
    # 创建课程表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        overall_grade TEXT,
        last_updated DATETIME
    )
    ''')
    
    # 创建任务日程表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT NOT NULL,
        due_time DATETIME,
        course_name TEXT,
        created_at DATETIME
    )
    ''')
    
    conn.commit()
    return conn

def update_database():
    """更新数据库中的信息"""
    conn = init_database()
    cursor = conn.cursor()
    
    # 初始化 ManageBac
    print("正在初始化 WebDriver...")
    mbscr = mb("xiangfeng20070726@163.com", "HuaGui_2007", hide_window=True, subdomain="h14z")
    
    try:
        # 登录
        print("正在登录...")
        mbscr.login()
        print("登录成功！")
        
        # 获取课程信息
        print("正在获取课程信息...")
        classes = mbscr.get_classes()
        
        # 清空现有课程数据
        cursor.execute("DELETE FROM courses")
        
        # 获取并存储课程总成绩
        for class_info in classes:
            try:
                grade_info = mbscr.get_overallgrades(target=class_info)
                # 将成绩信息格式化为字符串
                grade_str = str(grade_info.grades[0].number) if grade_info.grades else "N/A"
                
                cursor.execute('''
                INSERT INTO courses (course_name, overall_grade, last_updated)
                VALUES (?, ?, ?)
                ''', (class_info.name, grade_str, datetime.now()))
            except Exception as e:
                print(f"获取 {class_info.name} 成绩时出错: {e}")
        
        # 获取日程信息
        print("正在获取日程信息...")
        # 清空现有任务数据
        cursor.execute("DELETE FROM tasks")
        
        schedule = mbscr.get_schedule()
        # 注意：这里需要根据实际的 get_schedule() 返回格式调整处理逻辑
        # 这里假设返回的是任务列表，每个任务包含名称和截止时间
        for task in schedule:
            cursor.execute('''
            INSERT INTO tasks (task_name, due_time, created_at)
            VALUES (?, ?, ?)
            ''', (task.name, task.due_time, datetime.now()))
        
        conn.commit()
        print("数据库更新完成！")
        
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        mbscr.quit()
        conn.close()

def display_data():
    """显示数据库中的信息"""
    conn = sqlite3.connect('managebac.db')
    cursor = conn.cursor()
    
    print("\n=== 课程和总成绩 ===")
    cursor.execute("SELECT course_name, overall_grade FROM courses")
    for row in cursor.fetchall():
        print(f"课程: {row[0]}, 总成绩: {row[1]}")
    
    print("\n=== 未来两周的任务 ===")
    two_weeks_later = datetime.now() + timedelta(weeks=2)
    cursor.execute("""
    SELECT task_name, due_time, course_name 
    FROM tasks 
    WHERE due_time <= ? 
    ORDER BY due_time
    """, (two_weeks_later,))
    
    for row in cursor.fetchall():
        print(f"任务: {row[0]}, 截止时间: {row[1]}, 课程: {row[2] or '未指定'}")
    
    conn.close()

if __name__ == "__main__":
    update_database()
    display_data()