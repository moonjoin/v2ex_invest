import sys
import time
import feedparser
import requests
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QDateEdit
from PyQt6.QtCore import QTimer, Qt, QDate

class V2EXInvestReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_feed)
        
        # 添加日期选择器的信号连接
        self.start_date.dateChanged.connect(self.validate_date_range)
        self.end_date.dateChanged.connect(self.validate_date_range)
        
    def initUI(self):
        self.setWindowTitle('V2EX投资帖子阅读器')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建设置区域
        settings_layout = QHBoxLayout()
        
        # 添加日期范围选择
        date_range_label = QLabel('日期范围：')
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))  # 默认7天前
        self.start_date.setCalendarPopup(True)  # 启用日历弹出框
        self.start_date.setDisplayFormat('yyyy-MM-dd')  # 设置日期显示格式
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)  # 启用日历弹出框
        self.end_date.setDisplayFormat('yyyy-MM-dd')  # 设置日期显示格式
        
        # 添加快捷选项按钮
        quick_select_layout = QHBoxLayout()
        last_7_days = QPushButton('最近7天')
        last_30_days = QPushButton('最近30天')
        last_90_days = QPushButton('最近90天')
        
        last_7_days.clicked.connect(lambda: self.set_date_range(7))
        last_30_days.clicked.connect(lambda: self.set_date_range(30))
        last_90_days.clicked.connect(lambda: self.set_date_range(90))
        
        quick_select_layout.addWidget(last_7_days)
        quick_select_layout.addWidget(last_30_days)
        quick_select_layout.addWidget(last_90_days)
        
        # 设置按钮样式
        button_style = "QPushButton { padding: 5px 10px; border-radius: 3px; background-color: #f0f0f0; } QPushButton:hover { background-color: #e0e0e0; }"
        last_7_days.setStyleSheet(button_style)
        last_30_days.setStyleSheet(button_style)
        last_90_days.setStyleSheet(button_style)
        
        date_layout = QVBoxLayout()
        date_range_row = QHBoxLayout()
        date_range_row.addWidget(date_range_label)
        date_range_row.addWidget(self.start_date)
        date_range_row.addWidget(QLabel('至'))
        date_range_row.addWidget(self.end_date)
        date_range_row.addStretch()
        
        date_layout.addLayout(date_range_row)
        date_layout.addLayout(quick_select_layout)
        
        settings_layout.addLayout(date_layout)
        
        settings_layout.addStretch()
        layout.addLayout(settings_layout)
        
        # 创建文本显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # 创建按钮
        self.fetch_button = QPushButton('获取最新帖子')
        self.fetch_button.clicked.connect(self.fetch_feed)
        layout.addWidget(self.fetch_button)
        
    def log(self, message):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_area.append(f'[{current_time}] {message}')
        self.log_area.repaint()
        
    def fetch_feed(self):
        try:
            self.log('开始获取V2EX投资板块的RSS feed...')
            feed = feedparser.parse('https://www.v2ex.com/feed/invest.xml')
            
            # 获取用户设置的参数
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            self.log(f'设置参数：日期范围：{start_date} 至 {end_date}')
            
            output = []
            
            # 添加HTML头部和样式
            output.append('<!DOCTYPE html>')
            output.append('<html><head><meta charset="utf-8">')
            output.append('<style>')
            output.append('body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }')
            output.append('.post { background: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }')
            output.append('.post-title { font-size: 1.4em; color: #333; margin-bottom: 10px; }')
            output.append('.post-meta { color: #666; font-size: 0.9em; margin-bottom: 15px; }')
            output.append('.post-content { margin-bottom: 20px; }')
            output.append('.comments { background: #f9f9f9; padding: 15px; border-radius: 5px; }')
            output.append('.comment { border-bottom: 1px solid #eee; padding: 10px 0; position: relative; }')
            output.append('.comment:last-child { border-bottom: none; }')
            output.append('.comment-floor { position: absolute; right: 10px; top: 10px; color: #999; font-size: 0.9em; }')
            output.append('.author-comment { color: #ff4444; }')
            output.append('</style>')
            output.append('</head><body>')
            
            for entry in feed.entries:
                # 解析帖子发布时间
                published_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ').date()
                
                # 检查日期范围
                if start_date <= published_date <= end_date:
                    self.log(f'正在处理帖子: {entry.title}')
                    output.append('<div class="post">')
                    output.append(f'<h2 class="post-title"><a href="{entry.link}" target="_blank">{entry.title}</a></h2>')
                    output.append(f'<div class="post-meta">发布于 {entry.published}</div>')
                    output.append(f'<div class="post-content">{entry.description}</div>')
                    
                    # 创建用户名到楼层号的映射
                    username_to_floor = {}
                    
                    # 获取评论
                    retry_count = 0
                    max_retries = 3
                    retry_delay = 1  # 初始重试延迟（秒）
                    
                    while retry_count < max_retries:
                        try:
                            # 从链接中提取帖子ID
                            topic_id = entry.link.split('/')[-1]
                            comments_url = f'https://www.v2ex.com/api/replies/show.json?topic_id={topic_id}'
                            self.log(f'正在获取评论 (尝试 {retry_count + 1}/{max_retries})...')
                            
                            # 设置5秒超时
                            response = requests.get(comments_url, timeout=5)
                            comments = response.json()
                            
                            if comments:
                                output.append('<div class="comments">')
                                output.append('<h3>评论区:</h3>')
                                for i, comment in enumerate(comments, 1):
                                    comment_class = 'comment'
                                    if comment.get('member', {}).get('username') == entry.author:
                                        comment_class += ' author-comment'
                                    output.append(f'<div class="{comment_class}">')
                                    output.append(f'<div class="comment-floor">#{i}</div>')
                                    # 获取评论内容
                                    content = comment.get('content', '无内容')
                                    
                                    # 记录用户名和楼层号的对应关系
                                    username = comment.get('member', {}).get('username')
                                    if username:
                                        username_to_floor[username] = i
                                    
                                    # 替换@用户名为@楼层号
                                    for username, floor in username_to_floor.items():
                                        content = content.replace(f'@{username}', f'@#{floor}')
                                    
                                    output.append(content)
                                    output.append('</div>')
                                output.append('</div>')
                                self.log(f'成功获取 {len(comments)} 条评论')
                            break  # 成功获取评论，跳出重试循环
                            
                        except requests.Timeout:
                            retry_count += 1
                            if retry_count < max_retries:
                                self.log(f'获取评论超时，{retry_delay}秒后重试...')
                                time.sleep(retry_delay)
                                retry_delay *= 2  # 指数退避
                            else:
                                output.append('<div class="comments">获取评论失败: 请求超时</div>')
                                self.log('获取评论失败：达到最大重试次数')
                                
                        except Exception as e:
                            retry_count += 1
                            if retry_count < max_retries:
                                self.log(f'获取评论出错，{retry_delay}秒后重试...')
                                time.sleep(retry_delay)
                                retry_delay *= 2  # 指数退避
                            else:
                                output.append(f'<div class="comments">获取评论失败: {str(e)}</div>')
                                self.log('获取评论失败：达到最大重试次数')
                    
                    output.append('</div>')
            
            output.append('</body></html>')
            
            # 保存到文件
            filename = f'v2ex_invest_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output))
            
            self.log(f'成功保存帖子到文件: {filename}')
            
        except Exception as e:
            self.log(f'错误: {str(e)}')

    def set_date_range(self, days):
        """设置日期范围的快捷方法"""
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-days + 1)  # +1 是为了包含今天
        self.start_date.setDate(start_date)
        self.end_date.setDate(end_date)
    
    def validate_date_range(self):
        """验证并确保开始日期不晚于结束日期"""
        start = self.start_date.date()
        end = self.end_date.date()
        
        if start > end:
            # 如果开始日期晚于结束日期，将结束日期设置为开始日期
            self.end_date.setDate(start)

def main():
    app = QApplication(sys.argv)
    reader = V2EXInvestReader()
    reader.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()