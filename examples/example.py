from src import pymanagebac as mb
import sqlite3
from datetime import datetime, timedelta
import os
import re
from selenium.webdriver.common.by import By

# Set up SQLite database with error handling
def init_database():
    """初始化数据库并创建必要的表"""
    try:
        # 检查是否需要删除旧数据库文件
        if os.path.exists('managebac.db'):
            # 检查数据库架构是否需要更新
            try:
                temp_conn = sqlite3.connect('managebac.db')
                temp_cursor = temp_conn.cursor()
                
                # 检查courses表结构
                temp_cursor.execute("PRAGMA table_info(courses)")
                columns = [column[1] for column in temp_cursor.fetchall()]
                
                # 如果缺少新列，则删除数据库文件以重建架构
                if 'overall_percentage' not in columns:
                    temp_conn.close()
                    os.remove('managebac.db')
                    print("数据库架构已过时，正在重建数据库...")
                else:
                    temp_conn.close()
            except sqlite3.Error:
                # 如果无法检查架构，也删除旧数据库
                if os.path.exists('managebac.db'):
                    os.remove('managebac.db')
                print("数据库可能损坏，正在重建数据库...")
        
        conn = sqlite3.connect('managebac.db')
        cursor = conn.cursor()
        
        # 创建课程总表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            overall_grade TEXT,
            overall_percentage TEXT,
            last_updated DATETIME
        )
        ''')
        
        # 创建任务日程表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            due_date TEXT,
            due_time TEXT,
            course_name TEXT,
            description TEXT,
            created_at DATETIME
        )
        ''')
        
        conn.commit()
        print("数据库初始化成功")
        return conn, cursor
    except sqlite3.Error as e:
        print(f"数据库初始化错误: {e}")
        # 如果出错，尝试重新创建连接
        try:
            if conn:
                conn.close()
            # 如果数据库文件存在，尝试删除并重新创建
            if os.path.exists('managebac.db'):
                os.remove('managebac.db')
                print("删除旧数据库文件并重新创建...")
            return sqlite3.connect('managebac.db'), sqlite3.connect('managebac.db').cursor()
        except:
            print("无法恢复数据库连接，程序将退出")
            exit(1)

# 生成有效的SQL表名
def sanitize_table_name(name):
    """将课程名转换为有效的SQL表名"""
    # 移除所有非字母数字字符
    name = re.sub(r'[^\w]', '_', name)
    # 确保不以数字开头
    if name and name[0].isdigit():
        name = "course_" + name
    # 限制长度
    if len(name) > 50:
        name = name[:50]
    return name

# 异常处理装饰器
def handle_db_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            print(f"数据库操作错误: {e}")
            print(f"在函数 {func.__name__} 中发生")
            # 返回一个默认值或None
            return None
    return wrapper

# 初始化数据库
try:
    conn, cursor = init_database()
except Exception as e:
    print(f"严重错误: {e}")
    print("无法初始化数据库，程序将退出")
    exit(1)

# 安全执行SQL
@handle_db_exception
def safe_execute(cursor, sql, params=None):
    if params:
        return cursor.execute(sql, params)
    else:
        return cursor.execute(sql)

# 安全创建表
@handle_db_exception
def create_course_table(cursor, table_name):
    # 先检查表是否存在
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # 如果表存在，检查是否有所有需要的列
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 如果缺少必要列，删除旧表并重建
        if 'weight_percentage' not in columns or 'grade_percentage' not in columns:
            cursor.execute(f"DROP TABLE {table_name}")
            table_exists = False
    
    if not table_exists:
        safe_execute(cursor, f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_type TEXT NOT NULL,
            grade_value TEXT,
            grade_percentage TEXT,
            weight_percentage TEXT,
            max_grade TEXT,
            last_updated DATETIME
        )
        ''')

# 从成绩文本中提取百分比
def extract_percentage(grade_text):
    """从成绩文本中提取百分比"""
    if not grade_text:
        return None
    
    # 寻找括号中的百分比
    percentage_match = re.search(r'\(([0-9.]+)%\)', grade_text)
    if percentage_match:
        return percentage_match.group(1)
    return None

# 从成绩类型中提取权重百分比
def extract_weight(grade_type):
    """从成绩类型文本中提取权重百分比"""
    if not grade_type:
        return None
    
    # 寻找括号中的百分比权重
    weight_match = re.search(r'\(([0-9.]+)%\)', grade_type)
    if weight_match:
        return weight_match.group(1)
    return None

print("正在初始化WebDriver...")
try:
    mbscr = mb("xiangfeng20070726@163.com", "HuaGui_2007", hide_window=False, subdomain="h14z")
except Exception as e:
    print(f"初始化WebDriver失败: {e}")
    conn.close()
    exit(1)

print("logging in...")
try:
    # be sure to run this instantly because well you first need to log in
    mbscr.login()
    print("Successfully logged in!")
except Exception as e:
    print(f"登录失败: {e}")
    mbscr.quit()
    conn.close()
    exit(1)

print("getting classes...")
try:
    # we get all the classes that the student has. this is used to identify the ID of the class and use that as target for
    # the get_grades method
    classes = mbscr.get_classes()
    print("got classes!")
except Exception as e:
    print(f"获取课程列表失败: {e}")
    mbscr.quit()
    conn.close()
    exit(1)

valid_classes = []
temp = []

# 验证课程，确保课程名可以用作表名
for course in classes:
    table_name = sanitize_table_name(course.name)
    if table_name:
        course.safe_table_name = table_name  # 将安全的表名附加到课程对象
        valid_classes.append(course)
    else:
        print(f"警告: 跳过无效名称的课程: {course.name}")

print(f"有效课程数: {len(valid_classes)}/{len(classes)}")

print("getting overallgrades...")

# 清空现有课程数据
try:
    safe_execute(cursor, "DELETE FROM courses")
except Exception as e:
    print(f"清空课程数据失败: {e}")

# 为每个课程创建单独的表格
for course in valid_classes:
    try:
        create_course_table(cursor, course.safe_table_name)
    except Exception as e:
        print(f"为课程 {course.name} 创建表失败: {e}")

for i in range(0, len(valid_classes)):
    try:
        course_with_grades = mbscr.get_overallgrades(target=valid_classes[i])
        temp.append(course_with_grades)
        
        # 存储课程总体信息
        if course_with_grades.grades:
            overall_grade_obj = course_with_grades.grades[0]
            overall_grade = overall_grade_obj.number if hasattr(overall_grade_obj, 'number') else "N/A"
            percentage = extract_percentage(overall_grade)
        else:
            overall_grade = "N/A"
            percentage = None
        
        safe_execute(cursor, '''
        INSERT INTO courses (course_name, overall_grade, overall_percentage, last_updated)
        VALUES (?, ?, ?, ?)
        ''', (course_with_grades.name, overall_grade, percentage, datetime.now()))
        
        # 存储该课程的详细成绩信息
        table_name = valid_classes[i].safe_table_name
        
        # 先清空该课程的表
        try:
            safe_execute(cursor, f"DELETE FROM {table_name}")
        except Exception as e:
            print(f"清空课程 {course_with_grades.name} 表失败: {e}")
            continue
        
        # 插入详细成绩 (overall and subaspects)
        for grade in course_with_grades.grades:
            try:
                if hasattr(grade, 'number'):
                    grade_value = grade.number
                    grade_percentage = extract_percentage(grade_value)
                    grade_type = grade.name
                    weight = extract_weight(grade_type)
                    
                    safe_execute(cursor, f'''
                    INSERT INTO {table_name} (grade_type, grade_value, grade_percentage, weight_percentage, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (grade_type, grade_value, grade_percentage, weight, datetime.now()))
            except Exception as e:
                print(f"存储课程 {course_with_grades.name} 的成绩 {grade.name if hasattr(grade, 'name') else '未知'} 失败: {e}")
        
    except Exception as e:
        print(f"获取课程 {valid_classes[i].name} 的总体成绩失败: {e}")
        continue

print("got overallgrades! parsing output...")

for item in temp:
    print(f"\n\nclass: {item.name}")
    for i in item.grades:
        try:
            print(f"Grade type: {i.name}")
            print(f"Score: {i.number}")
        except AttributeError:
            print(f"无法显示该成绩项目")

print("getting assignments...")
# 清空现有任务数据
try:
    safe_execute(cursor, "DELETE FROM assignments")
except Exception as e:
    print(f"清空任务数据失败: {e}")

# 获取日程信息
try:
    mbscr.get_schedule()
    driver = mbscr.driver
    event_texts = driver.find_elements(By.CLASS_NAME, "mb-event__text")
    
    for event_text in event_texts:
        try:
            info = event_text.text
            
            # 获取日期
            try:
                date_element = event_text.find_element(By.XPATH, "ancestor::td[@data-date]")
                due_date = date_element.get_attribute("data-date")
            except Exception:
                print("无法获取日期，跳过此作业")
                continue
            
            # 获取时间和作业内容
            try:
                due_time = event_text.find_element(By.TAG_NAME, "strong").text
            except Exception:
                due_time = "未指定"
            
            try:
                assignment_content = event_text.find_element(By.TAG_NAME, "div").text
            except Exception:
                # 如果找不到div，尝试使用完整的文本
                assignment_content = info
            
            # 尝试从作业内容中提取课程名称
            course_name = None
            for course in valid_classes:
                if course.name in info:
                    course_name = course.name
                    break
            
            # 只存储未来两周内的任务
            try:
                assignment_date = datetime.strptime(due_date, "%Y-%m-%d")
                if assignment_date <= datetime.now() + timedelta(weeks=2):
                    safe_execute(cursor, '''
                    INSERT INTO assignments (task_name, due_date, due_time, course_name, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (assignment_content, due_date, due_time, course_name, info, datetime.now()))
                
                print(f"日期: {due_date}, 截止时间: {due_time}, 课程: {course_name or '未知'}, 作业内容: {assignment_content}")
            except Exception as e:
                print(f"处理作业日期时出错: {e}")
                print(f"完整信息: {info}")
        except Exception as e:
            print(f"处理单个作业时出错: {e}")
            continue
except Exception as e:
    print(f"获取作业时出错: {e}")

# 获取详细成绩
detail_grades_temp = []
for i in range(0, len(valid_classes)):
    try:
        course_with_grades = mbscr.get_grades(target=valid_classes[i])
        detail_grades_temp.append(course_with_grades)
        
        # 存储该课程的详细作业成绩
        table_name = valid_classes[i].safe_table_name
        
        for grade in course_with_grades.grades:
            try:
                if hasattr(grade, 'grade'):
                    grade_value = str(grade.grade) if grade.grade else "N/A"
                    max_grade = str(grade.max_grade) if hasattr(grade, 'max_grade') and grade.max_grade else "N/A"
                    
                    safe_execute(cursor, f'''
                    INSERT INTO {table_name} (grade_type, grade_value, max_grade, last_updated)
                    VALUES (?, ?, ?, ?)
                    ''', (grade.name, grade_value, max_grade, datetime.now()))
                
            except Exception as e:
                print(f"存储课程 {course_with_grades.name} 的详细成绩失败: {e}")
            
    except Exception as e:
        print(f"获取课程 {valid_classes[i].name} 的详细成绩失败: {e}")
        continue

print("got grades! parsing output...")

# sometimes the teacher will submit a non-myp grade, in that case the grade is not a dictionary but in a list
# in this block code we use the output of the get_grades method to determine if the grade is a dictionary -> myp
# or something custom. after that we print the grade for that class including its name of class and the assignment name
for item in detail_grades_temp:
    print(f"\n\nclass: {item.name}")
    for i in item.grades:
        try:
            if hasattr(i, 'grade'):
                grade = i.grade
                max_grade = i.max_grade if hasattr(i, 'max_grade') else None
                print(f"Name Assignment: {i.name}")

                if isinstance(i.grade, dict):
                    keys = i.grade.keys()
                    if "A" in keys:
                        print(f"criteria A: {i.grade.get('A')}")
                    if "B" in keys:
                        print(f"criteria B: {i.grade.get('B')}")
                    if "C" in keys:
                        print(f"criteria C: {i.grade.get('C')}")
                    if "D" in keys:
                        print(f"criteria D: {i.grade.get('D')}")
                else:
                    print(f"Your Grade: {grade} out of {max_grade}")
            elif hasattr(i, 'number'):
                # 处理a_overgrade对象，这种对象有number但没有grade属性
                print(f"Grade type: {i.name}")
                print(f"Score: {i.number}")
            else:
                print("未知的成绩类型")
        except Exception as e:
            print(f"处理成绩显示时出错: {e}")

# 显示数据库中存储的信息
def display_database_info():
    print("\n=== 数据库中存储的信息 ===")
    
    try:
        print("\n--- 课程总表 ---")
        result = safe_execute(cursor, "SELECT course_name, overall_grade, overall_percentage FROM courses")
        if result:
            rows = result.fetchall()
            for row in rows:
                percentage_display = f" ({row[2]}%)" if row[2] else ""
                print(f"课程: {row[0]}, 总成绩: {row[1]}{percentage_display}")
        else:
            print("无法获取课程信息")
    except Exception as e:
        print(f"显示课程信息时出错: {e}")
    
    try:
        print("\n--- 未来两周的作业任务 ---")
        result = safe_execute(cursor, """
        SELECT task_name, due_date, due_time, description, course_name 
        FROM assignments 
        ORDER BY due_date, due_time
        """)
        if result:
            rows = result.fetchall()
            for row in rows:
                print(f"任务: {row[0]}, 日期: {row[1]}, 时间: {row[2]}, 课程: {row[4] or '未指定'}")
                print(f"描述: {row[3]}\n")
        else:
            print("无法获取作业任务信息")
    except Exception as e:
        print(f"显示作业任务时出错: {e}")
    
    try:
        print("\n--- 各课程详细成绩 ---")
        result = safe_execute(cursor, "SELECT course_name FROM courses")
        if result:
            courses = result.fetchall()
            
            for course in courses:
                course_name = course[0]
                # 寻找对应的表名
                table_name = None
                for c in valid_classes:
                    if c.name == course_name:
                        table_name = c.safe_table_name
                        break
                
                if not table_name:
                    print(f"无法找到课程 {course_name} 的表名")
                    continue
                
                print(f"\n{course_name} 详细成绩:")
                try:
                    result = safe_execute(cursor, f"""
                    SELECT grade_type, grade_value, grade_percentage, weight_percentage, max_grade 
                    FROM {table_name}
                    ORDER BY id
                    """)
                    if result:
                        grades = result.fetchall()
                        for grade in grades:
                            grade_type = grade[0]
                            grade_value = grade[1]
                            grade_percentage = grade[2]
                            weight_percentage = grade[3]
                            max_grade = grade[4]
                            
                            # 构造漂亮的输出格式
                            percentage_display = f" ({grade_percentage}%)" if grade_percentage else ""
                            weight_display = f" [{weight_percentage}%]" if weight_percentage else ""
                            max_display = f" / {max_grade}" if max_grade and max_grade != "N/A" else ""
                            
                            print(f"  {grade_type}{weight_display}: {grade_value}{percentage_display}{max_display}")
                    else:
                        print(f"  无法获取 {course_name} 的成绩")
                except Exception as e:
                    print(f"  无法访问 {course_name} 的成绩表: {e}")
        else:
            print("无法获取课程列表")
    except Exception as e:
        print(f"显示课程详细成绩时出错: {e}")

# 提交所有更改到数据库
try:
    conn.commit()
    print("\n所有数据已成功保存到数据库")
except Exception as e:
    print(f"提交数据库更改时出错: {e}")

# 显示数据库信息
display_database_info()

# you NEED to call this function for the webdriver to quit
try:
    mbscr.quit()
except Exception as e:
    print(f"关闭WebDriver时出错: {e}")

# 关闭数据库连接
try:
    conn.close()
    print("数据库连接已关闭")
except Exception as e:
    print(f"关闭数据库连接时出错: {e}")
