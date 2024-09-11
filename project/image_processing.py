import cv2
import numpy as np
from typing import List, Tuple

def is_near_white(color, threshold=210):
    # 判斷一個顏色是否接近白色，使用給定的閾值
    return np.all(color > threshold)

def image_to_binary_matrix(image_path, threshold=210):
    # 讀取圖像
    image = cv2.imread(image_path)
    image = cv2.resize(image, (500, 500))  # 調整圖像大小為500x500
    # 獲取圖像的高度和寬度
    height, width = image.shape[:2]
    
    # 創建一個同樣大小的二維矩陣
    binary_matrix = np.zeros((height, width), dtype=int)
    
    # 遍歷每個像素點
    for y in range(height):
        for x in range(width):
            # 獲取像素點的顏色
            color = image[y, x]
            # 判斷顏色是否接近白色
            if is_near_white(color, threshold):
                binary_matrix[y, x] = 0
            else:
                binary_matrix[y, x] = 1
    
    # 將 numpy.ndarray 轉換為 list
    binary_list = binary_matrix.tolist()
    
    return binary_list, image

def largest_rectangle_in_histogram(heights, row_index):
    # 計算直方圖中最大的矩形
    stack = []  # 用於儲存直方圖的索引
    rectangles = []  # 用於儲存找到的矩形
    heights.append(0)  # 添加哨兵值以便處理剩餘矩形

    for i in range(len(heights)):
        # 當堆疊不為空且當前高度小於堆疊頂部的高度時
        while stack and heights[i] < heights[stack[-1]]:
            h = heights[stack.pop()]  # 獲取堆疊頂部的高度
            # 計算矩形的寬度
            w = i if not stack else i - stack[-1] - 1
            if h > 0:
                # 儲存矩形的起始行、起始列、結束行和結束列
                rectangles.append((row_index - h + 1, stack[-1] + 1 if stack else 0, row_index, i - 1))
        stack.append(i)  # 將當前索引添加到堆疊中
    heights.pop()  # 移除哨兵值

    return rectangles  # 返回找到的矩形

def maximal_rectangle(matrix: List[List[int]]) -> List[Tuple[int, int, int, int]]:
    # 計算二進位矩陣中最大的矩形
    if not matrix:
        return []

    rectangles = []  # 用於儲存找到的矩形
    dp = [0] * len(matrix[0])  # 直方圖高度的動態規劃數組
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            # 更新直方圖高度
            dp[j] = dp[j] + 1 if matrix[i][j] == 1 else 0

        # 計算此行直方圖的最大矩形
        rects = largest_rectangle_in_histogram(dp, i)

    return rectangles  # 返回所有找到的矩形

def find_rectangles(grid):
    # 函數目的：找出二維矩陣中的所有矩形
    rows, cols = len(grid), len(grid[0])  # 獲取矩陣的行數和列數
    rectangles = []  # 用於存儲找到的矩形

    def find_max_rectangle(start_row, start_col):
        # 函數目的：找出從指定起始點開始的最大矩形的寬度和高度
        max_width = 0  # 最大寬度初始化為 0
        max_height = 0  # 最大高度初始化為 0

        # 找出最大寬度
        for col in range(start_col, cols):
            if grid[start_row][col] == 1:
                max_width += 1  # 如果矩陣中值為 1，增加寬度
            else:
                break  # 遇到值為 0，停止增加寬度

        # 找出最大高度
        for row in range(start_row, rows):
            if all(grid[row][col] == 1 for col in range(start_col, start_col + max_width)):
                max_height += 1  # 如果在指定寬度範圍內的所有值都為 1，增加高度
            else:
                break  # 若不全為 1，停止增加高度

        return max_width, max_height  # 返回最大寬度和最大高度

    # 遍歷矩陣中的每個元素
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] == 1:  # 如果發現矩陣中的值為 1
                width, height = find_max_rectangle(row, col)  # 找到以該點為起始點的最大矩形的寬度和高度
                rectangles.append((row, col, width, height))  # 將找到的矩形的起始點、寬度和高度添加到列表中

                # 標記已訪問的區域，將該矩形範圍內的所有值設置為 0，表示已訪問
                for r in range(row, row + height):
                    for c in range(col, col + width):
                        grid[r][c] = 0

    return rectangles  # 返回所有找到的矩形列表
 