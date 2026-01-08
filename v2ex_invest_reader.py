import sys
import time
import feedparser
import requests
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QDateEdit, QLineEdit, QFileDialog, QCheckBox, QGroupBox
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
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建设置区域
        settings_group = QGroupBox('导出设置')
        settings_layout = QVBoxLayout(settings_group)
        
        # 日期范围选择区域
        date_layout = QHBoxLayout()
        date_range_label = QLabel('日期范围：')
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))  # 默认7天前
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat('yyyy-MM-dd')
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat('yyyy-MM-dd')
        
        date_layout.addWidget(date_range_label)
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel('至'))
        date_layout.addWidget(self.end_date)
        date_layout.addStretch()
        
        # 快捷选项按钮
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
        quick_select_layout.addStretch()
        
        # 设置按钮样式
        button_style = "QPushButton { padding: 5px 10px; border-radius: 3px; background-color: #f0f0f0; } QPushButton:hover { background-color: #e0e0e0; }"
        last_7_days.setStyleSheet(button_style)
        last_30_days.setStyleSheet(button_style)
        last_90_days.setStyleSheet(button_style)
        
        # 导出目录设置
        export_dir_layout = QHBoxLayout()
        export_dir_label = QLabel('导出目录：')
        self.export_dir_input = QLineEdit()
        self.export_dir_input.setPlaceholderText('默认为当前目录')
        self.export_dir_input.setText(os.getcwd())  # 默认当前目录
        
        browse_button = QPushButton('浏览...')
        browse_button.clicked.connect(self.browse_export_dir)
        browse_button.setStyleSheet(button_style)
        
        export_dir_layout.addWidget(export_dir_label)
        export_dir_layout.addWidget(self.export_dir_input)
        export_dir_layout.addWidget(browse_button)
        
        # 导出格式选项
        export_format_layout = QHBoxLayout()
        export_format_label = QLabel('导出格式：')
        self.html_checkbox = QCheckBox('HTML格式')
        self.html_checkbox.setChecked(True)
        self.ai_json_checkbox = QCheckBox('AI阅读JSON格式')
        self.ai_json_checkbox.setChecked(True)
        
        export_format_layout.addWidget(export_format_label)
        export_format_layout.addWidget(self.html_checkbox)
        export_format_layout.addWidget(self.ai_json_checkbox)
        export_format_layout.addStretch()
        
        settings_layout.addLayout(date_layout)
        settings_layout.addLayout(quick_select_layout)
        settings_layout.addLayout(export_dir_layout)
        settings_layout.addLayout(export_format_layout)
        
        layout.addWidget(settings_group)
        
        # 创建文本显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # 创建按钮
        button_layout = QHBoxLayout()
        self.fetch_button = QPushButton('获取并导出帖子')
        self.fetch_button.clicked.connect(self.fetch_feed)
        self.fetch_button.setStyleSheet("QPushButton { padding: 10px; background-color: #007bff; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #0056b3; }")
        
        self.clear_log_button = QPushButton('清空日志')
        self.clear_log_button.clicked.connect(self.clear_log)
        self.clear_log_button.setStyleSheet(button_style)
        
        button_layout.addWidget(self.fetch_button)
        button_layout.addWidget(self.clear_log_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
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
            export_dir = self.export_dir_input.text().strip()
            
            # 检查导出目录是否存在
            if not export_dir:
                export_dir = os.getcwd()
            elif not os.path.exists(export_dir):
                self.log(f'导出目录不存在: {export_dir}，将使用当前目录')
                export_dir = os.getcwd()
            
            # 检查导出格式选项
            export_html = self.html_checkbox.isChecked()
            export_ai_json = self.ai_json_checkbox.isChecked()
            
            if not export_html and not export_ai_json:
                self.log('错误: 请至少选择一种导出格式')
                return
            
            self.log(f'设置参数：日期范围：{start_date} 至 {end_date}')
            self.log(f'导出目录：{export_dir}')
            self.log(f'导出格式：HTML={export_html}, AI JSON={export_ai_json}')
            
            # 收集所有帖子数据
            posts_data = {
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "posts": []
            }
            
            # HTML输出
            html_output = []
            html_output.append('<!DOCTYPE html>')
            html_output.append('<html><head><meta charset="utf-8">')
            html_output.append('<style>')
            html_output.append('body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }')
            html_output.append('.post { background: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }')
            html_output.append('.post-title { font-size: 1.4em; color: #333; margin-bottom: 10px; }')
            html_output.append('.post-meta { color: #666; font-size: 0.9em; margin-bottom: 15px; }')
            html_output.append('.post-content { margin-bottom: 20px; }')
            html_output.append('.comments { background: #f9f9f9; padding: 15px; border-radius: 5px; }')
            html_output.append('.comment { border-bottom: 1px solid #eee; padding: 10px 0; position: relative; }')
            html_output.append('.comment:last-child { border-bottom: none; }')
            html_output.append('.comment-floor { position: absolute; right: 10px; top: 10px; color: #999; font-size: 0.9em; }')
            html_output.append('.author-comment { color: #ff4444; }')
            html_output.append('</style>')
            html_output.append('</head><body>')
            
            processed_count = 0
            
            for entry in feed.entries:
                # 解析帖子发布时间
                published_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ').date()
                
                # 检查日期范围
                if start_date <= published_date <= end_date:
                    self.log(f'正在处理帖子: {entry.title}')
                    processed_count += 1
                    
                    # 收集帖子数据
                    post_data = {
                        "id": entry.link.split('/')[-1],
                        "title": entry.title,
                        "author": entry.author,
                        "published": entry.published,
                        "link": entry.link,
                        "summary": entry.description,
                        "comments": []
                    }
                    
                    # HTML输出
                    html_output.append('<div class="post">')
                    html_output.append(f'<h2 class="post-title"><a href="{entry.link}" target="_blank">{entry.title}</a></h2>')
                    html_output.append(f'<div class="post-meta">发布于 {entry.published}</div>')
                    html_output.append(f'<div class="post-content">{entry.description}</div>')
                    
                    # 创建用户名到楼层号的映射
                    username_to_floor = {}
                    
                    # 获取评论
                    retry_count = 0
                    max_retries = 3
                    retry_delay = 1
                    
                    while retry_count < max_retries:
                        try:
                            topic_id = entry.link.split('/')[-1]
                            comments_url = f'https://www.v2ex.com/api/replies/show.json?topic_id={topic_id}'
                            self.log(f'正在获取评论 (尝试 {retry_count + 1}/{max_retries})...')
                            
                            response = requests.get(comments_url, timeout=5)
                            comments = response.json()
                            
                            if comments:
                                html_output.append('<div class="comments">')
                                html_output.append('<h3>评论区:</h3>')
                                
                                for i, comment in enumerate(comments, 1):
                                    comment_class = 'comment'
                                    is_author_comment = comment.get('member', {}).get('username') == entry.author
                                    if is_author_comment:
                                        comment_class += ' author-comment'
                                    
                                    html_output.append(f'<div class="{comment_class}">')
                                    html_output.append(f'<div class="comment-floor">#{i}</div>')
                                    
                                    content = comment.get('content', '无内容')
                                    username = comment.get('member', {}).get('username')
                                    
                                    if username:
                                        username_to_floor[username] = i
                                    
                                    # 替换@用户名为@楼层号
                                    for username, floor in username_to_floor.items():
                                        content = content.replace(f'@{username}', f'@#{floor}')
                                    
                                    html_output.append(content)
                                    html_output.append('</div>')
                                    
                                    # 收集评论数据
                                    comment_data = {
                                        "floor": i,
                                        "author": comment.get('member', {}).get('username', '匿名'),
                                        "content": comment.get('content', '无内容'),
                                        "is_author_comment": is_author_comment
                                    }
                                    post_data["comments"].append(comment_data)
                                
                                html_output.append('</div>')
                                self.log(f'成功获取 {len(comments)} 条评论')
                            
                            break
                            
                        except requests.Timeout:
                            retry_count += 1
                            if retry_count < max_retries:
                                self.log(f'获取评论超时，{retry_delay}秒后重试...')
                                time.sleep(retry_delay)
                                retry_delay *= 2
                            else:
                                html_output.append('<div class="comments">获取评论失败: 请求超时</div>')
                                self.log('获取评论失败：达到最大重试次数')
                                
                        except Exception as e:
                            retry_count += 1
                            if retry_count < max_retries:
                                self.log(f'获取评论出错，{retry_delay}秒后重试...')
                                time.sleep(retry_delay)
                                retry_delay *= 2
                            else:
                                html_output.append(f'<div class="comments">获取评论失败: {str(e)}</div>')
                                self.log('获取评论失败：达到最大重试次数')
                    
                    html_output.append('</div>')
                    posts_data["posts"].append(post_data)
            
            html_output.append('</body></html>')
            
            # 生成文件名
            base_filename = f'v2ex_invest_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}'
            
            # 保存HTML文件
            if export_html:
                html_filename = os.path.join(export_dir, f'{base_filename}.html')
                with open(html_filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(html_output))
                self.log(f'成功保存HTML文件: {html_filename}')
            
            # 保存AI JSON文件
            if export_ai_json and posts_data["posts"]:
                ai_json_data = self.generate_ai_json(posts_data)
                ai_json_filename = os.path.join(export_dir, f'{base_filename}_ai.json')
                with open(ai_json_filename, 'w', encoding='utf-8') as f:
                    json.dump(ai_json_data, f, ensure_ascii=False, indent=2)
                self.log(f'成功保存AI JSON文件: {ai_json_filename}')
            
            if processed_count == 0:
                self.log('在指定日期范围内没有找到帖子')
            else:
                self.log(f'处理完成，共处理 {processed_count} 个帖子')
            
        except Exception as e:
            self.log(f'错误: {str(e)}')

    def set_date_range(self, days):
        """设置日期范围的快捷方法"""
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-days + 1)  # +1 是为了包含今天
        self.start_date.setDate(start_date)
        self.end_date.setDate(end_date)
    
    def browse_export_dir(self):
        """浏览选择导出目录"""
        directory = QFileDialog.getExistingDirectory(self, '选择导出目录', self.export_dir_input.text())
        if directory:
            self.export_dir_input.setText(directory)
    
    def clear_log(self):
        """清空日志区域"""
        self.log_area.clear()
    
    def validate_date_range(self):
        """验证并确保开始日期不晚于结束日期"""
        start = self.start_date.date()
        end = self.end_date.date()
        
        if start > end:
            # 如果开始日期晚于结束日期，将结束日期设置为开始日期
            self.end_date.setDate(start)
    
    def generate_ai_json(self, posts_data):
        """生成AI阅读定制的JSON格式"""
        ai_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "source": "V2EX投资板块",
                "date_range": {
                    "start": posts_data["date_range"]["start"],
                    "end": posts_data["date_range"]["end"]
                },
                "total_posts": len(posts_data["posts"])
            },
            "posts": []
        }
        
        for post in posts_data["posts"]:
            ai_post = {
                "id": post["id"],
                "title": post["title"],
                "author": post["author"],
                "published": post["published"],
                "link": post["link"],
                "summary": post["summary"],
                "key_points": self.extract_key_points(post["summary"]),
                "sentiment": self.analyze_sentiment(post["summary"]),
                "tags": self.extract_tags(post["title"], post["summary"]),
                "comments": []
            }
            
            for comment in post["comments"]:
                ai_comment = {
                    "floor": comment["floor"],
                    "author": comment["author"],
                    "content": comment["content"],
                    "is_author_comment": comment.get("is_author_comment", False),
                    "key_points": self.extract_key_points(comment["content"]),
                    "sentiment": self.analyze_sentiment(comment["content"]),
                    "mentioned_floors": self.extract_mentions(comment["content"])
                }
                ai_post["comments"].append(ai_comment)
            
            ai_data["posts"].append(ai_post)
        
        return ai_data
    
    def extract_key_points(self, text):
        """提取关键点（简化的关键词提取）"""
        if not text:
            return []
        
        # 简化的关键词提取 - 可以根据需要扩展
        keywords = []
        important_words = ['投资', '股票', '基金', '市场', '收益', '风险', '分析', '建议', '推荐', '买入', '卖出', '涨', '跌']
        
        for word in important_words:
            if word in text:
                keywords.append(word)
        
        return keywords[:5]  # 最多返回5个关键词
    
    def analyze_sentiment(self, text):
        """简单的情感分析"""
        if not text:
            return "neutral"
        
        positive_words = ['好', '涨', '赚', '推荐', '买入', '看好', '收益', '机会', '利好']
        negative_words = ['差', '跌', '亏', '风险', '卖出', '看空', '利空', '危险', '亏损']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count + 2:
            return "positive"
        elif negative_count > positive_count + 2:
            return "negative"
        else:
            return "neutral"
    
    def extract_tags(self, title, content):
        """提取标签"""
        tags = []
        
        # 从标题和内容中提取可能的标签
        tag_candidates = ['A股', '港股', '美股', '基金', '股票', '投资', '理财', '加密货币', '比特币', '黄金', '房地产']
        
        full_text = title + " " + content
        for tag in tag_candidates:
            if tag in full_text:
                tags.append(tag)
        
        # 如果没有找到预定义标签，提取一些关键词
        if not tags:
            words = full_text.split()
            important_words = [w for w in words if len(w) > 1 and w.isalnum()]
            tags = list(set(important_words))[:3]  # 最多3个标签
        
        return tags
    
    def extract_mentions(self, content):
        """提取@的楼层号"""
        import re
        mentions = []
        
        # 匹配 @#数字 的格式
        pattern = r'@#(\d+)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            mentions.append(int(match))
        
        return mentions

def main():
    app = QApplication(sys.argv)
    reader = V2EXInvestReader()
    reader.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()