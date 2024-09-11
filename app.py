from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap5
from flask_mysqldb import MySQL
from config import Config
from werkzeug.utils import secure_filename
from image_processing import image_to_binary_matrix, find_rectangles
import cv2
import os

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)  # 調用 init_app 方法來創建必要的目錄
bootstrap = Bootstrap5(app)

app.app_context().push()

mysql = MySQL(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query')
def query():
    return render_template('query.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password or not name:
            return "請完整填寫所有字段", 400
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO `users` (`name`, `email`, `password`) VALUES (%s, %s, %s);", (name, email, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))
    else:
        return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("請完整填寫所有字段", "error")
            return render_template('login.html'), 400
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user:
            user_id, user_name, user_password, user_email = user
            
            if user_password == password:
                session['id'] = user_id
                session['name'] = user_name
                flash("登錄成功!", "success")
                return redirect(url_for('index'))
            else:
                flash("郵箱或密碼錯誤", "error")
        else:
            flash("郵箱或密碼錯誤", "error")
        
        return render_template('login.html'), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'id' in session:
        session.clear()
        flash("您已成功登出", "success")
    else:
        flash("您尚未登錄", "info")
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_img():
    if request.method == 'POST':
        if 'img' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('img')
        if not files or all(f.filename == '' for f in files):
            flash("請選擇至少一張圖片", "error")
            return redirect(request.url)

        grouped_data = {}  # 用於存儲分組數據
        image_data = []  # 用於存儲所有圖片的數據   
            
        for f in files:
            if f and allowed_file(f.filename):
                material = f.filename.split('_')
                #去除檔案後贅字
                material[1] = material[1].rstrip('.JPGjpgjpegpng')
                filename = secure_filename(f.filename)

                original_filename = f"uploads_{material[0]}_{material[1]}.jpg"
                original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                

                try:
                    f.save(original_filepath)
                    print(f"File saved successfully: {original_filepath}")
                except Exception as e:
                    print(f"Error saving file: {str(e)}")
                    flash(f"無法保存文件 {filename}", "error")
                    continue

                if not os.path.exists(original_filepath):
                    print(f"Failed to save file: {original_filepath}")
                    flash(f"無法保存文件 {filename}", "error")
                    continue

                # 處理圖片    
                try:
                    binary_list, image = image_to_binary_matrix(original_filepath)

                    # 處理邊界，保留原有的邏輯
                    for i in range(len(binary_list) - 1):
                        count = 0
                        for j in range(len(binary_list[0]) - 1):
                            if binary_list[i][j + 1] == 0: count += 1
                            if binary_list[i + 1][j] == 0: count += 1
                            if binary_list[i + 1][j + 1] == 0: count += 1
                            if count >= 1: binary_list[i][j] = 0

                    # 初始化最小和最大座標
                    min_x, min_y = float('inf'), float('inf')
                    max_x, max_y = 0, 0

                    rectangles = find_rectangles(binary_list)
                    rectangles_info = []

                    for i, rectangle in enumerate(rectangles):
                        y, x, width, height = rectangle
                        area = width * height

                        if area > 200 and width > 1: 
                            cv2.rectangle(image, (x, y), (x + width, y + height), (0, 255, 0), 2)  # 繪製綠色矩形

                            rectangle_info = {
                                "編號": i + 1,
                                "面積": area,
                                "x": x,
                                "y": y,
                                "長": height,
                                "寬": width,
                                "材質": material[1],  # 使用 1 表示材質
                                "板材編號": material[0]
                            }

                            rectangles_info.append(rectangle_info)

                            # 更新最小和最大座標
                            min_x = min(min_x, x)
                            min_y = min(min_y, y)
                            max_x = max(max_x, x + width)
                            max_y = max(max_y, y + height)

                    # 確保有有效的矩形
                    if min_x < float('inf') and min_y < float('inf'):
                        # 計算最小外接矩形的長和寬
                        enclosing_width = max_x - min_x
                        enclosing_height = max_y - min_y

                        # 在圖像上繪製最小外接矩形
                        cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 0, 0), 2)  # 使用藍色(255, 0, 0)

                        # 加入分組邏輯和總面積的計算
                        for rectangle in rectangles_info:
                            plate_number = rectangle['板材編號']
                            area = rectangle['面積']

                            if plate_number not in grouped_data:
                                grouped_data[plate_number] = {
                                    "材質": rectangle['材質'],
                                    "總面積": area,
                                    "偵測結果": [],
                                    "最小外接矩形": {
                                        "length": enclosing_height,
                                        "width": enclosing_width
                                    }
                                }
                            else:
                                grouped_data[plate_number]["總面積"] += area

                            grouped_data[plate_number]["偵測結果"].append({
                                "長": rectangle['長'],
                                "寬": rectangle['寬'],
                                "x": rectangle['x'],
                                "y": rectangle['y'],
                                "面積": area
                            })

                        output_filename = f"output_{material[0]}_{material[1]}.jpg"
                        output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

                        success = cv2.imwrite(output_filepath, image)
                        if success:
                            image_data.append({
                                "scrap_id": material[0],  # 板材編號
                                "material": material[1],  # 材質
                                "estimated_size": str(sum(rect["面積"] for rect in rectangles_info)),  # 預估大小
                                "detection_results": rectangles_info,  # 偵測結果
                                "minimum_bounding_rectangle": {"length": enclosing_height, "width": enclosing_width},  # 最小外接矩形
                                "original_image": f"uploads/{original_filename}",  # 原圖
                                "processed_image": f"outputs/{output_filename}"  # 處理後圖
                            })
                    else:
                        print("未找到有效的矩形。")
                        
                except Exception as e:
                    print(f"處理圖片 {original_filepath} 時發生錯誤: {str(e)}")
                    flash(f"處理圖片 {original_filepath} 時發生錯誤", "error")
                    continue
                
        if image_data:
            return render_template('result.html', image_data=image_data)
        else:
            flash("沒有成功處理任何圖片", "warning")
            return redirect(request.url)

    return render_template('upload_img.html')

@app.route('/read', methods=['GET', 'POST'])
def read():
    if request.method == 'POST':
        # 从表单获取查询条件
        material_id = request.form.get('material_id')
        material_type = request.form.get('material_type')
        estimated_size = request.form.get('estimated_size')
        rectangle_length = request.form.get('rectangle_length')
        rectangle_width = request.form.get('rectangle_width')

        # 构建SQL查询语句，使用LIKE匹配部分输入内容
        query = "SELECT * FROM materials WHERE 1=1"
        filters = []
        if material_id:
            query += " AND material_id LIKE %s"
            filters.append(f"%{material_id}%")
        if material_type:
            query += " AND material_type LIKE %s"
            filters.append(f"%{material_type}%")
        if estimated_size:
            query += " AND estimated_size >= %s"
            filters.append(estimated_size)
        if rectangle_length:
            query += " AND rectangle_length >= %s"
            filters.append(rectangle_length)
        if rectangle_width:
            query += " AND rectangle_width >= %s"
            filters.append(rectangle_width)
        
        cur = mysql.connection.cursor()
        cur.execute(query, filters)
        results = cur.fetchall()
        cur.close()

        # 如果找到结果，将其传递给模板
        if results:
            flash(f"共找到 {len(results)} 條記錄", "success")
        else:
            flash("未找到匹配的記錄", "info")
        
        return render_template('results.html', results=results)
    
    # 如果是GET请求，渲染查询表单页面
    return render_template('read.html')



if __name__ == '__main__':
    app.run(port= 5000, debug=True)