from src import pymanagebac as mb

# we make the pymanagebac object, it should automatically find your subdomain if not you can add the subdomain parameter
# automatically runs in headless if you want to see the window add hidewindow=True as argument
# 请将下面的 "YOUR_EMAIL" 和 "YOUR_PASSWORD" 替换为您的 ManageBac 登录信息
print("正在初始化WebDriver...")
mbscr = mb("xiangfeng20070726@163.com", "HuaGui_2007", hide_window=True,subdomain="h14z")


print("logging in...")

# be sure to run this instantly because well you first need to log in
mbscr.login()
print("Successfully logged in!")

print("getting classes...")
# we get all the classes that the student has. this is used to identify the ID of the class and use that as target for
# the get_grades method
classes = mbscr.get_classes()
print("got classes!")

temp = []

print("getting overallgrades...")

for i in range(0, len(classes)):
    try:
        temp.append(mbscr.get_overallgrades(target=classes[i]))
    except Exception as e:
        print(f"Error getting overallgrades for class {classes[i].name}: {e}")
        continue

print("got overallgrades! parsing output...")

for item in temp:
    print(f"\n\nclass: {item.name}")
    for i in item.grades:
        print(f"Grade type: {i.name}")
        print(f"Score: {i.number}")

print("getting assignments...")
mbscr.get_schedule()
# self.driver.get(f"https://{self.subdomain}.managebac.cn/student/calendar")
# sleep(1)
# # 直接查找所有的mb-event__text元素
# event_texts = self.driver.find_elements(By.CLASS_NAME, "mb-event__text")

# for event_text in event_texts:
#     # 获取元素内的文本，这会包含时间和作业内容
#     info = event_text.text
    
#             # 如果需要分别获取时间和作业内容
#             # 时间在<strong>标签内
#     try:
#         due_time = event_text.find_element(By.TAG_NAME, "strong").text
#         # 作业内容在<div>标签内
#         assignment_content = event_text.find_element(By.TAG_NAME, "div").text
        
#         print(f"截止时间: {due_time}, 作业内容: {assignment_content}")
#     except:
#         print(f"完整信息: {info}")

# we get all the grades for all the classes of the student using our output of the get_classes method
for i in range(0, len(classes)):
    temp.append(mbscr.get_grades(target=classes[i]))

print("got grades! parsing output...")

# sometimes the teacher will submit a non-myp grade, in that case the grade is not a dictionary but in a list
# in this block code we use the output of the get_grades method to determine if the grade is a dictionary -> myp
# or something custom. after that we print the grade for that class including its name of class and the assignment name
for item in temp:
    print(f"\n\nclass: {item.name}")
    for i in item.grades:
        grade = i.grade
        max_grade = i.max_grade
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

# you NEED to call this function for the webdriver to quit
mbscr.quit()
