import re
import requests as req
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.firefox.options import Options
import bs4


class classe:
    def __init__(self, class_id: int, name: str, grade: list):
        """
        :type class_id: int
        :type name: str
        :type grade: list
        """

        self.class_id = class_id
        self.grades = grade
        self.name = name
    
class a_overgrade:
    def __init__(self, name: str, number: str):
        """_summary_

        Args:
            number (str): 分数
            name (str): 名称（overall，subaspects）
        """
        self.number = number
        self.name = name

class a_grade:
    def __init__(self, number: str, max_number: str, name: str):
        """
        :type number: str
        :type name: str
        """
        self.grade = number
        self.max_grade = max_number
        self.name = name


class a_task:
    def __init__(self, date, title: str, description: str):
        """

        :type date: str
        :type title: str
        :type description: str
        """
        self.date = date
        self.description = description
        self.name = title


class pymanagebac:
    def __init__(self, mail: str, password: str, impl_wait=5., hide_window=False, subdomain="" , logging_level=None):

        def get_subdomain(mail2):
            to_ret = []
            first_if = False
            for i in mail2:
                if i == "@" or first_if:
                    if not first_if:
                        first_if = True
                        continue

                    if i == ".":
                        break
                    to_ret.append(i)

            ret = ""
            for i in to_ret:
                ret += i

            return ret

        self.options = None
        if hide_window:
            self.options = Options()
            self.options.add_argument("--headless")

        self.driver = webdriver.Firefox(options=self.options)
        self.mail = mail
        if subdomain:
            self.subdomain = subdomain
        else:
            self.subdomain = get_subdomain(mail)
        self.password = password
        self.driver.implicitly_wait(impl_wait)
        self.session_cookie = None

    def login(self):
        """
        Login to the student site
        Returns:

        """
        self.driver.get(f"https://{self.subdomain}.managebac.cn/student")
        self.driver.find_element(By.ID, "session_login").send_keys(self.mail)
        self.driver.find_element(By.ID, "session_password").send_keys(self.password)
        self.driver.find_element(By.NAME, "commit").click()

    def get_schedule(self):
        """
        Get the schedule of the day
        Returns: list of classes that you have that day.

        """
        self.driver.get(f"https://{self.subdomain}.managebac.cn/student/calendar")
        sleep(1)
    # 直接查找所有的mb-event__text元素
        event_texts = self.driver.find_elements(By.CLASS_NAME, "mb-event__text")

        for event_text in event_texts:
            # 获取元素内的文本，这会包含时间和作业内容
            info = event_text.text
            date_element = event_text.find_element(By.XPATH, "ancestor::td[@data-date]")
            date_value = date_element.get_attribute("data-date")
            print(f"日期是: {date_value}")  # 应该输出 2025-04-03
    
            # 如果需要分别获取时间和作业内容
            # 时间在<strong>标签内
            try:
                due_time = event_text.find_element(By.TAG_NAME, "strong").text
                # 作业内容在<div>标签内
                assignment_content = event_text.find_element(By.TAG_NAME, "div").text
        
                print(f"截止时间: {due_time}, 作业内容: {assignment_content}")
            except:
                print(f"完整信息: {info}")
#        elements = self.driver.find_elements(By.CLASS_NAME, "fc-time-grid-event.fc-v-event.fc-event.fc-start.fc-end."
        eventbuttons= self.driver.find_element(By.CLASS_NAME, "fi fi-info mb-event__hint-icon")
        # fc-event

        ret_list = []
        my_text = ""
        for i in eventbuttons:
            ActionChains(self.driver).move_to_element(i).perform()
            my_text = i.get_attribute("title")
            ret_list.append(my_text)

        return ret_list

    def get_classes(self, target=1):
        """
        Get all the classes that the user has
        Args:
            target: 1 academic, 0 diploma (not used in current implementation)

        Returns:
            a list of objects of classes
        """
        # 使用新的URL直接访问课程页面
        self.driver.get(f"https://{self.subdomain}.managebac.cn/student/classes/my")
        sleep(1)  # 等待页面加载
        
        # 使用页面内容找到所有课程卡片
        page_source = self.driver.page_source
        soup = bs4.BeautifulSoup(page_source, features="html.parser")
        
        # 查找所有课程卡片元素 - 基于提供的开发者工具截图
        class_cards = soup.find_all("div", class_="fusion-card-item fusion-card-item-collapse ib-class-component")
        
        to_ret = []
        for card in class_cards:
            # 使用卡片的id属性提取课程ID
            class_id = 0
            if 'id' in card.attrs:
                id_value = card.attrs['id']
                if id_value.startswith('ib_class_'):
                    class_id = int(id_value.replace('ib_class_', ''))
            
            # 尝试从卡片中找到课程名称 - 使用类似您XPath路径的查找方式
            class_name = "Unknown Class"
            name_element = card.find("h4")
            if name_element and name_element.find("span") and name_element.find("span").find("a"):
                class_name = name_element.find("span").find("a").text.strip()
            
            if class_id > 0:
                to_ret.append(classe(class_id, class_name, []))
                print(f"Found class: {class_name} ({class_id})")
        
        # 如果上面的方法没有找到任何课程，尝试使用XPath
        if not to_ret:
            try:
                # 使用提供的XPath路径
                xpath = "/html/body/main/div[2]/div[2]/div[4]/div[1]/div[1]/div[1]/h4/span/a"
                elements = self.driver.find_elements(By.XPATH, xpath)
                
                for element in elements:
                    href = element.get_attribute("href")
                    class_name = element.text.strip()
                    
                    # 从href中提取课程ID
                    if href and "/student/classes/" in href:
                        class_id = int(href.split("/")[-1])
                        to_ret.append(classe(class_id, class_name, []))
            except Exception as e:
                print(f"Error using XPath: {e}")
        
        return to_ret
    
    def get_overallgrades(self, target: classe):
        """
        Get the overall grades for a specific class
        Args:
            target: the class that we want to look the grades for
        """
        grades = []#里面每个元素都是a_overallgrade类，其中第一个元素是overallscore，其他的是分别的子score
        self.driver.get(f"https://{self.subdomain}.managebac.cn/student/classes/{target.class_id}/core_tasks")
        soup = bs4.BeautifulSoup(self.driver.page_source, features="html.parser")
        grades_list = soup.find("div", class_="sidebar-items-list")#所有成绩的列表，那一栏，父div
        grades_div_first = grades_list.find_all("div", class_="list-item")[1]
        cells = grades_div_first.find_all("div", class_="cell")#第一个成绩的cell(overallscore)
        grade_name = cells[0].find("strong").text.strip()  # 第一个 cell 包含名称
        grade_score = cells[1].text.strip()  # 第二个 cell 包含分数
        grades.append(a_overgrade(grade_name, grade_score))
        grades_div = grades_list.find_all("div", class_="list-item")[2:]#那一栏的每个成绩，子div
        for grade in grades_div:
            cells = grade.find_all("div", class_="cell")
            grade_name = cells[0].find("div", class_="label").text.strip()  # 从 label 类中获取名称
            
            if len(cells) > 1:  # 确保有第二个cell
                score_cell = cells[1]
                # 检查是否有strong标签
                if score_cell.find('strong'):
                    grade_score = f"{score_cell.find('strong').text.strip()} {score_cell.text.strip().strip('() ')}"
                else:
                    grade_score = score_cell.text.strip() if score_cell.text.strip() else "暂无成绩"
            else:
                grade_score = "暂无成绩"
            
            grades.append(a_overgrade(grade_name, grade_score))
        target.grades = grades
        return target


    def get_grades(self, target: classe, term: int = 0):
        """
        Get the grades for a specific class
        Args:
            target: the class that we want to look the grades for
            term: the term that is getting scraped

        Returns:
            a list of a_grade objects, also changes the a_grade member of the classe to the classes that it found
        """
        self.driver.get(f"https://{self.subdomain}.managebac.cn/student/classes/{target.class_id}/core_tasks")

        # # getting the name of the page. that's also the class name
        # soup = bs4.BeautifulSoup(self.driver.page_source, features="html.parser")
        # name = soup.select("div h2")[0]
        # name = name.contents[0].strip()
        # target.name = name

        # 选择学期
        # terms_list = self.driver.find_element(By.ID, "current-term-grades-select")
        # terms = terms_list.find_element(By.TAG_NAME, "optgroup").find_elements(By.TAG_NAME, "option")
        # if term != 0:
        #     terms[term].click()
        # else:
        #     # get the last term
        #     terms[-1].click()

        soup = bs4.BeautifulSoup(self.driver.page_source, features="html.parser")
        grades = []
        tasks = soup.find_all("table", attrs={"class": "table table-hover table-striped student-term-report-table"})[0]\
            .find("tbody")

        tasks_all = tasks.find_all("tr")
        for task in tasks_all:
            attr1 = task.find_all("td", attrs={"class": "term-grade-task-name"})[0]
            title = attr1.a.text.replace("\t", "").replace("\n", "")
            try:
                grade_html = task.find_all("td", attrs={"class": "term-grade-max-score"})
                grade = task.find_all("td", attrs={"class": "term-grade-score"})

                if len(grade_html) and len(grade):
                    max_grade = grade_html[0].text.replace("\t", "").replace("\n", "").replace(" ", "")
                    grade = grade[0].text.replace("\t", "").replace("\n", "").replace(" ", "")

                    # sometimes the teacher, will not use the myp grading system.
                    # when the teacher do this the grades dont have the MYP format
                    if title.strip() != "":
                        criteria_html = task.find_all("td", attrs={"class": "term-grade-criterias"})
                        if len(criteria_html):
                            criteria = criteria_html[0].find_all("div", attrs={"class": "progress-bar-flex-group"})
                            if len(criteria):
                                to_ret = {}
                                for i in criteria:
                                    to_ret[i.find("strong").text] = i.find("span").text.replace(" ", "")
                                grades.append(a_grade(to_ret, max_grade, title))
                                continue

                        grades.append(a_grade(grade, max_grade, title))
            except:
                pass

        target.grades = grades
        return target

    def quit(self):
        """
        End the session
        Returns:
        """
        self.driver.quit()


if __name__ == "__main__":
    print("this is something you should import, not run directly")
