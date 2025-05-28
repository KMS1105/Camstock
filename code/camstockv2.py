import tkinter as tk
from tkinter import ttk
import random
from tkinter import messagebox
from tkinter.font import Font
import os

# 전역 변수 초기화
stocks = ['오만전자', 'LNG에너지', 'NEVER', '키커오', '현재차']
prices = {
    '오만전자': 50000,
    'LNG에너지': 40000,
    'NEVER': 30000,
    '키커오': 20000,
    '현재차': 10000
}
variation = {
    '오만전자': [-1500, 1500],
    'LNG에너지': [-1000, 1000],
    'NEVER': [-500, 500],
    '키커오': [-100, 100],
    '현재차': [-50, 50]
}
holdings = {s: {'qty': 0, 'avg_price': 0} for s in stocks}
balance = 1_000_000 # 초기 잔고 설정
ohlc = {s: [] for s in stocks}
candle_window = {s: {'open': prices[s], 'high': None, 'low': None, 'close': None, 'cnt': 0} for s in stocks}
selected_stock = stocks[0]
bankrupt_stocks = [] # 파산한 종목을 저장할 리스트

# Global variables for after() IDs, initialized to None
update_market_id = None
update_balance_id = None

# Global variable for zoom level
zoom_level = 1.0

# --- 업적 관련 전역 변수 및 함수 ---
ACHIEVEMENTS_FILE = 'achievements.txt'
achievements = set() # 달성한 업적을 저장할 set (중복 방지)

# Dictionary to map achievement keys to display names
achievement_display_names = {
    "balance_3m": "🏆 업적1: 부자 등극! (잔고 300만원 달성)",
    "balance_0": "💀 업적2: 알거지! (잔고 0원 이하)",
    "bankrupt_1_company": "🚧 업적3: 첫 번째 희생자 (1개 회사 파산)",
    "bankrupt_2_companies": "🚧 업적4: 두 번째 희생자 (2개 회사 파산)",
    "bankrupt_3_companies": "🚧 업적5: 세 번째 희생자 (3개 회사 파산)",
    "bankrupt_4_companies": "🚧 업적6: 네 번째 희생자 (4개 회사 파산)",
    "bankrupt_5_companies": "💀 업적7: 위기 전문가 (5개 회사 파산)",
    "all_bankrupt": "🔥 업적-1: 세상의 종말 (모든 회사 파산)",
}


def load_achievements():
    global achievements
    if os.path.exists(ACHIEVEMENTS_FILE):
        with open(ACHIEVEMENTS_FILE, 'r', encoding='utf-8') as f:
            achievements = {line.strip() for line in f if line.strip()}
    else:
        achievements = set()

def save_achievements():
    with open(ACHIEVEMENTS_FILE, 'w', encoding='utf-8') as f:
        for ach in sorted(list(achievements)):
            f.write(ach + '\n')

def unlock_achievement(key, message):
    if key not in achievements:
        achievements.add(key)
        messagebox.showinfo("🏆 업적 달성! 🏆", message)
        save_achievements()
        update_balance_text() # Update balance tab which shows achievements
        update_achievement_text() # Update the new achievement tab


# --- UI 구성 ---
root = tk.Tk()
root.title("Camstock")
root.geometry("600x800")
root.configure(bg='white')

# --- Bottom Navigation Bar ---
bottom_notebook = ttk.Notebook(root)
bottom_notebook.pack(side='top', fill='x')

bottom_notebook.add(ttk.Frame(bottom_notebook), text="주문")
bottom_notebook.add(ttk.Frame(bottom_notebook), text="차트")
bottom_notebook.add(ttk.Frame(bottom_notebook), text="잔고")
# Removed "조작" (Manipulation) tab
bottom_notebook.add(ttk.Frame(bottom_notebook), text="업적") # 업적 탭 추가

# --- Top Bar (Stock Info) ---
top_bar_frame = tk.Frame(root, bg='white', bd=1, relief='solid')
top_bar_frame.pack(side='top', fill='x', padx=5, pady=5)

tk.Label(top_bar_frame, text="종목명", font=('Arial', 10), bg='white').pack(side='left', padx=5)
stock_cb = ttk.Combobox(top_bar_frame, values=stocks, state='readonly', width=15)
stock_cb.pack(side='left', padx=5)
stock_cb.current(0)

price_label = tk.Label(top_bar_frame, text="", font=('Arial', 16, 'bold'), bg='white', anchor='e')
price_label.pack(side='right', padx=5, expand=True)

# --- Main Content Area ---
main_content_frame = tk.Frame(root, bg='white')
main_content_frame.pack(expand=True, fill='both', padx=5, pady=5)

# --- Define Content Frames ---
# --- Order Content Frame ---
order_content_frame = tk.Frame(main_content_frame, bg='white')

order_tab_main_frame = tk.Frame(order_content_frame, bg='white')
order_tab_main_frame.pack(expand=True, fill='both')

# Left: Order Book
order_book_frame = tk.Frame(order_tab_main_frame, bg='lightgray', width=300)
order_book_frame.pack(side='left', fill='y', padx=5, pady=5)
order_book_frame.pack_propagate(False)

tk.Label(order_book_frame, text="호가", font=('Arial', 12), bg='lightgray').pack(pady=5)

order_book_display_frame = tk.Frame(order_book_frame, bg='lightgray')
order_book_display_frame.pack(expand=True, fill='both', padx=5, pady=5)

order_book_font = Font(family='Consolas', size=10)
order_book_text = tk.Text(order_book_display_frame, font=order_book_font, bg='lightgray', wrap='none', width=20)
order_book_text.pack(side='left', fill='y', expand=False)

order_book_bar_canvas = tk.Canvas(order_book_display_frame, bg='lightgray', bd=0, highlightthickness=0)
order_book_bar_canvas.pack(side='right', fill='both', expand=True)

# Right: Buy/Sell Tabs
trade_notebook = ttk.Notebook(order_tab_main_frame)
trade_notebook.pack(side='right', expand=True, fill='both', padx=5, pady=5)

# --- Buy Tab ---
buy_tab = ttk.Frame(trade_notebook)
trade_notebook.add(buy_tab, text="매수")

tk.Label(buy_tab, text="수량", font=('Arial', 10)).pack(pady=(10,2))
buy_qty_entry = tk.Entry(buy_tab)
buy_qty_entry.pack()

tk.Button(buy_tab, text="현금 매수", bg='red', fg='white', font=('Arial', 12, 'bold'), command=lambda: place_order('buy')).pack(pady=20, fill='x', padx=20)

# --- Sell Tab ---
sell_tab = ttk.Frame(trade_notebook)
trade_notebook.add(sell_tab, text="매도")

tk.Label(sell_tab, text="수량", font=('Arial', 10)).pack(pady=(10,2))
sell_qty_entry = tk.Entry(sell_tab)
sell_qty_entry.pack()

tk.Button(sell_tab, text="현금 매도", bg='blue', fg='white', font=('Arial', 12, 'bold'), command=lambda: place_order('sell')).pack(pady=20, fill='x', padx=20)

# --- Chart Content Frame ---
chart_content_frame = tk.Frame(main_content_frame, bg='white')
chart_canvas = tk.Canvas(chart_content_frame, bg='white', bd=0, highlightthickness=0)
chart_canvas.pack(expand=True, fill='both')

# --- Balance Content Frame ---
balance_content_frame = tk.Frame(main_content_frame, bg='white')
balance_text = tk.Text(balance_content_frame, font=('Consolas', 12), bg='white')
balance_text.pack(fill='both', expand=True, padx=5, pady=5)

# Removed Manipulation Content Frame and its widgets/functions
# --- Achievement Content Frame ---
achievement_content_frame = tk.Frame(main_content_frame, bg='white')
achievement_text = tk.Text(achievement_content_frame, font=('Consolas', 12), bg='white')
achievement_text.pack(fill='both', expand=True, padx=5, pady=5)


# --- Functions ---
def update_price_label(event=None):
    global selected_stock
    selected_stock = stock_cb.get()
    if selected_stock in bankrupt_stocks:
        price_label.config(text=f"파산!", fg='red')
        order_book_text.delete('1.0', 'end')
        order_book_text.insert('end', f"{selected_stock} 파산\n거래 불가")
        order_book_bar_canvas.delete("all")
        return

    current = prices[selected_stock]
    ohlc_data = ohlc[selected_stock]
    prev = ohlc_data[-1][0] if ohlc_data else current
    if not ohlc_data and candle_window[selected_stock]['close'] is not None:
        prev = candle_window[selected_stock]['close']

    diff = current - prev
    diff_rate = (diff / prev * 100) if prev != 0 else 0

    color = 'red' if diff > 0 else 'blue' if diff < 0 else 'black'
    sign = '+' if diff > 0 else ''
    price_label.config(
        text=f"{current:,.0f} ({sign}{diff:,.0f} {sign}{diff_rate:.2f}%)",
        fg=color
    )
    root.update_idletasks()
    update_order_book_placeholder()


def update_order_book_placeholder():
    stock = selected_stock
    order_book_text.delete('1.0', 'end')
    order_book_bar_canvas.delete("all")
    
    line_height = order_book_font.metrics('linespace')
    current_line = 0

    order_book_text.insert('end', f"--- {stock} 호가 ---\n")
    current_line += 1

    if stock in bankrupt_stocks:
        order_book_text.insert('end', f"파산으로 거래 불가")
        current_line += 1
        return

    current_price = prices[stock]
    asks = []
    bids = []

    # Simulate market depth
    for i in range(1, 6):
        ask_price = current_price + i * random.randint(1, 10)
        ask_qty = random.randint(1000, 10000)
        asks.append((ask_price, ask_qty))

        bid_price = current_price - i * random.randint(1, 10)
        bid_qty = random.randint(1000, 10000)
        bids.append((bid_price, bid_qty))
    
    asks.sort()
    bids.sort(key=lambda x: x[0], reverse=True)

    all_quantities = [qty for _, qty, *rest in asks + bids]
    max_qty = max(all_quantities) if all_quantities else 1

    canvas_width = order_book_bar_canvas.winfo_width() if order_book_bar_canvas.winfo_width() > 0 else 100
    
    # Display asks and draw bars
    for price, qty, *is_pending in asks:
        tag = 'red_order'
        bar_color = '#fd9999'
        
        order_book_text.insert('end', f"{price:,.0f} | {qty:,.0f}\n", (tag,))
        
        y_center = current_line * line_height + (line_height / 2)
        y1 = y_center - (line_height / 2) + 2
        y2 = y_center + (line_height / 2) - 2
        
        bar_width = (qty / max_qty) * canvas_width
        order_book_bar_canvas.create_rectangle(0, y1, bar_width, y2, fill=bar_color, outline=bar_color)
        current_line += 1
    
    order_book_text.insert('end', f"------------------\n")
    current_line += 1

    order_book_text.insert('end', f"현재가: {current_price:,.0f}\n", ('current_price',))
    current_line += 1

    order_book_text.insert('end', f"------------------\n")
    current_line += 1

    # Display bids and draw bars
    for price, qty, *is_pending in bids:
        tag = 'blue_order'
        bar_color = '#9999df'
        
        order_book_text.insert('end', f"{price:,.0f} | {qty:,.0f}\n", (tag,))
        
        y_center = current_line * line_height + (line_height / 2)
        y1 = y_center - (line_height / 2) + 2
        y2 = y_center + (line_height / 2) - 2
        
        bar_width = (qty / max_qty) * canvas_width
        order_book_bar_canvas.create_rectangle(0, y1, bar_width, y2, fill=bar_color, outline=bar_color)
        current_line += 1

    order_book_text.tag_config('red_order', foreground='red')
    order_book_text.tag_config('blue_order', foreground='blue')
    order_book_text.tag_config('current_price', foreground='green', font=('Consolas', 10, 'bold'))


def place_order(side):
    global balance
    stock = selected_stock
    if stock in bankrupt_stocks:
        messagebox.showerror("주문 오류", f"{stock}은(는) 파산하여 거래할 수 없습니다.")
        return

    if side == 'buy':
        qty_entry_ref = buy_qty_entry
    else: # side == 'sell'
        qty_entry_ref = sell_qty_entry

    try:
        qty = int(qty_entry_ref.get())
        if qty <= 0:
            messagebox.showwarning("주문 오류", "수량은 0보다 커야 합니다.")
            return

        price = prices[stock] 
    except ValueError:
        messagebox.showwarning("입력 오류", "수량을 올바르게 입력해주세요.")
        return

    total_price = qty * price

    if side == 'buy':
        if balance < total_price:
            messagebox.showerror("잔고 부족", "잔고가 부족하여 매수를 실행할 수 없습니다.")
            return
        h = holdings[stock]
        total_cost = h['avg_price'] * h['qty'] + qty * price
        h['qty'] += qty
        h['avg_price'] = total_cost / h['qty']
        balance -= qty * price
        messagebox.showinfo("주문 체결", f"시장가 매수 {stock} {qty}주 @ {price:,.0f}원 체결되었습니다.")
        print(f"[시장가 체결] 매수 {stock} {qty}주 @ {price:,.0f}원")
    elif side == 'sell':
        if holdings[stock]['qty'] < qty:
            messagebox.showerror("수량 부족", "보유한 주식이 부족하여 매도를 실행할 수 없습니다.")
            return
        holdings[stock]['qty'] -= qty
        if holdings[stock]['qty'] == 0:
            holdings[stock]['avg_price'] = 0
        balance += qty * price
        messagebox.showinfo("주문 체결", f"시장가 매도 {stock} {qty}주 @ {price:,.0f}원 체결되었습니다.")
        print(f"[시장가 체결] 매도 {stock} {qty}주 @ {price:,.0f}원")

    update_balance_text()
    update_order_book_placeholder()


def update_balance_text():
    balance_text.delete('1.0', 'end')
    balance_text.insert('end', f"보유 잔고: {balance:,.0f} 원\n\n")
    balance_text.insert('end', f"보유 종목:\n")
    for s in sorted(stocks + bankrupt_stocks, key=lambda x: (x in bankrupt_stocks, x)):
        if s in bankrupt_stocks:
            balance_text.insert('end', f"  {s}: 파산됨\n", ('red',))
            continue

        h = holdings[s]
        if h['qty'] > 0:
            cur_price = prices[s]
            profit = (cur_price - h['avg_price']) * h['qty']
            color = 'red' if profit > 0 else 'blue' if profit < 0 else 'black'
            sign = '+' if profit > 0 else ''
            balance_text.insert('end', f"  {s}: {h['qty']}주 / 매입가 {h['avg_price']:,.0f}원 / 현재가 {cur_price:,.0f}원\n", ('normal',))
            balance_text.insert('end', f"  손익: {sign}{profit:,.0f}원\n", (color,))
        else:
            if s in prices:
                balance_text.insert('end', f"  {s}: 보유 없음\n", ('normal',))

    balance_text.tag_config('red', foreground='red')
    balance_text.tag_config('blue', foreground='blue')
    balance_text.tag_config('normal', foreground='black')
    balance_text.tag_config('achievement', foreground='green', font=('Consolas', 12, 'bold'))

def update_achievement_text():
    achievement_text.delete('1.0', 'end')
    achievement_text.insert('end', "--- 달성 업적 ---\n\n")
    if not achievements:
        achievement_text.insert('end', " 아직 달성한 업적이 없습니다.\n")
    else:
        for key in sorted(list(achievements)):
            display_name = achievement_display_names.get(key, f"알 수 없는 업적: {key}")
            achievement_text.insert('end', f" {display_name}\n", ('achievement',))
    achievement_text.tag_config('achievement', foreground='green', font=('Consolas', 12, 'bold'))


def draw_chart(stock):
    global zoom_level
    if not chart_canvas.winfo_ismapped():
        return

    if stock in bankrupt_stocks:
        chart_canvas.delete("all")
        chart_canvas.create_text(chart_canvas.winfo_width()/2, chart_canvas.winfo_height()/2,
                                 text=f"{stock} 파산", fill="red", font=('Arial', 24))
        return

    data = list(ohlc[stock])
    w_data = candle_window[stock]
    if w_data['cnt'] > 0 and w_data['close'] is not None:
        data.append((w_data['open'], w_data['high'], w_data['low'], w_data['close']))

    chart_canvas.delete("all")
    w = chart_canvas.winfo_width()
    h = chart_canvas.winfo_height()
    margin = 20
    
    display_candles = int(30 / zoom_level)
    if display_candles < 5:
        display_candles = 5
    
    display_data = data[-display_candles:] # 리스트 슬라이싱 수정

    if not display_data:
        chart_canvas.create_text(w/2, h/2, text="차트 데이터 없음", fill="gray")
        return

    all_prices = [v for c in display_data for v in c if v is not None]
    if not all_prices:
        chart_canvas.create_text(w/2, h/2, text="차트 데이터 없음", fill="gray")
        return

    maxp, minp = max(all_prices), min(all_prices)
    if maxp == minp:
        maxp += 1
        minp -= 1
    scale = (h - 2 * margin) / (maxp - minp + 1e-5)

    bw = (w - 2 * margin) / display_candles * 0.6

    for i, (o, hi, lo, c) in enumerate(display_data):
        if any(v is None for v in [o, hi, lo, c]):
            continue

        x = margin + i * ((w - 2 * margin) / display_candles) + ((w - 2 * margin) / display_candles) / 2
        y_o = h - margin - (o - minp) * scale
        y_c = h - margin - (c - minp) * scale
        y_h = h - margin - (hi - minp) * scale
        y_l = h - margin - (lo - minp) * scale
        color = 'red' if c >= o else 'blue'
        
        if i == len(display_data) - 1 and w_data['cnt'] > 0 and stock == selected_stock:
            color = '#ff9999' if c >= o else '#9999ff'
        
        chart_canvas.create_line(x, y_h, x, y_l, fill='black')
        chart_canvas.create_rectangle(x - bw/2, y_o, x + bw/2, y_c, fill=color, outline='black')


def zoom_chart(event):
    global zoom_level
    if bottom_notebook.tab(bottom_notebook.select(), "text") != "차트":
        return

    if event.delta > 0 or event.num == 4: # Scroll up (zoom in)
        zoom_level *= 1.1
    elif event.delta < 0 or event.num == 5: # Scroll down (zoom out)
        zoom_level /= 1.1

    if zoom_level < 0.5:
        zoom_level = 0.5
    if zoom_level > 5.0:
        zoom_level = 5.0
        
    draw_chart(selected_stock)


def update_market():
    global update_market_id
    global balance, stocks, bankrupt_stocks

    # --- 게임 종료 조건 및 업적 확인 ---
    if balance >= 3_000_000:
        unlock_achievement("balance_3m", "🏆 업적1: 부자 등극! (잔고 300만원 달성)")
    elif balance <= 0:
        unlock_achievement("balance_0", "💀 업적2: 알거지! (잔고 0원 이하)")
    
    num_bankrupt = len(bankrupt_stocks)
    if num_bankrupt >= 1:
        unlock_achievement("bankrupt_1_company", "🚧 업적3: 첫 번째 희생자 (1개 회사 파산)")
    if num_bankrupt >= 2:
        unlock_achievement("bankrupt_2_companies", "🚧 업적4: 두 번째 희생자 (2개 회사 파산)")
    if num_bankrupt >= 3:
        unlock_achievement("bankrupt_3_companies", "🚧 업적5: 세 번째 희생자 (3개 회사 파산)")
    if num_bankrupt >= 4:
        unlock_achievement("bankrupt_4_companies", "🚧 업적6: 네 번째 희생자 (4개 회사 파산)")
    if num_bankrupt >= 5:
        unlock_achievement("bankrupt_5_companies", "💀 업적7: 위기 전문가 (5개 회사 파산)")


    current_stocks = list(stocks)

    for stock in current_stocks:
        if stock in bankrupt_stocks:
            continue

        w = candle_window[stock]
        prev = w['close'] if w['close'] is not None else w['open']
        delta = random.choice(variation[stock])
        price = max(1, prev + delta)
        prices[stock] = price

        # 파산 로직: 주가가 1원이고 30% 확률로 파산
        if price == 1 and random.random() < 0.3:
            messagebox.showinfo("🚨 주식 파산 알림 🚨", f"{stock}이(가) 파산했습니다!\n보유 중이던 {stock} 주식은 모두 사라집니다.")
            bankrupt_stocks.append(stock)
            if stock in stocks:
                stocks.remove(stock)
            if holdings[stock]['qty'] > 0:
                holdings[stock]['qty'] = 0
                holdings[stock]['avg_price'] = 0
            
            stock_cb['values'] = stocks
            # Removed manipulation_stock_cb update
            if stocks:
                stock_cb.current(0)
                # Removed manipulation_stock_cb.set(stocks[0])
                global selected_stock
                selected_stock = stocks[0]
            else: # 모든 종목이 파산한 경우
                stock_cb.set("모든 종목 파산")
                stock_cb['state'] = 'disabled'
                # Removed manipulation_stock_cb.set("모든 종목 파산")
                # Removed manipulation_stock_cb['state'] = 'disabled'
                unlock_achievement("all_bankrupt", "🔥 업적-1: 세상의 종말 (모든 회사 파산)")
                messagebox.showinfo("게임 종료", "모든 종목이 파산하여 더 이상 거래할 수 없습니다.\n게임을 종료합니다.")
                if update_market_id:
                    root.after_cancel(update_market_id)
                if update_balance_id:
                    root.after_cancel(update_balance_id)
                root.quit()
                return

        if w['cnt'] == 0:
            w['open'] = price
            w['high'] = price
            w['low'] = price
        else:
            w['high'] = max(w['high'], price)
            w['low'] = min(w['low'], price)
        w['close'] = price
        w['cnt'] += 1

        if w['cnt'] >= 10:
            ohlc[stock].append((w['open'], w['high'], w['low'], w['close']))
            if len(ohlc[stock]) > 30:
                ohlc[stock].pop(0)
            w['cnt'] = 0
            w['open'] = price
            w['high'] = price
            w['low'] = price
            w['close'] = price

    update_price_label()
    update_balance_text()
    update_achievement_text() # Call to update the achievement tab
    if bottom_notebook.tab(bottom_notebook.select(), "text") == "차트":
        draw_chart(selected_stock)
    
    # Removed manipulation tab update
    # if bottom_notebook.tab(bottom_notebook.select(), "text") == "조작":
    #     update_manip_price_label()
    #     current_balance_label.config(text=f"현재 잔고: {balance:,.0f}원")


    update_market_id = root.after(1000, update_market)

# Function to show/hide content frames based on bottom tab selection
def show_tab_content(event):
    selected_tab_text = bottom_notebook.tab(bottom_notebook.select(), "text")

    order_content_frame.pack_forget()
    chart_content_frame.pack_forget()
    balance_content_frame.pack_forget()
    # Removed manipulation_content_frame.pack_forget()
    achievement_content_frame.pack_forget() # Hide the new achievement frame

    if selected_tab_text == "주문":
        order_content_frame.pack(expand=True, fill='both')
        update_order_book_placeholder() 
    elif selected_tab_text == "차트":
        chart_content_frame.pack(expand=True, fill='both')
        draw_chart(selected_stock)
    elif selected_tab_text == "잔고":
        balance_content_frame.pack(expand=True, fill='both')
        update_balance_text()
    # Removed "조작" tab condition
    # elif selected_tab_text == "조작":
    #     manipulation_content_frame.pack(expand=True, fill='both')
    #     update_manip_price_label()
    #     current_balance_label.config(text=f"현재 잔고: {balance:,.0f}원") # 조작 탭 선택 시 잔고 레이블 업데이트
    elif selected_tab_text == "업적": # New tab condition
        achievement_content_frame.pack(expand=True, fill='both')
        update_achievement_text() # Update achievement text when tab is selected

# Initial display for the "주문" tab
show_tab_content(None)

# Event listeners
stock_cb.bind("<<ComboboxSelected>>", update_price_label)
bottom_notebook.bind("<<NotebookTabChanged>>", show_tab_content)

# Bind mouse wheel events to the chart canvas
chart_canvas.bind("<MouseWheel>", zoom_chart)
chart_canvas.bind("<Button-4>", zoom_chart)
chart_canvas.bind("<Button-5>", zoom_chart)

# Start market updates
load_achievements() # 게임 시작 시 업적 로드
update_price_label()
update_balance_id = root.after(100, update_balance_text)
update_market_id = root.after(1000, update_market)
root.mainloop()
