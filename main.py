from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import datetime
import database
import uvicorn
from contextlib import asynccontextmanager
from export_excel import export_orders_to_excel_and_email

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    customer_name: str
    contact: str
    address: str
    memo: Optional[str] = ""
    items: List[OrderItem]

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
async def read_admin():
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/products")
async def get_products():
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE is_active=1")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

@app.post("/api/orders")
async def create_order(order: OrderCreate):
    conn = database.get_db()
    cursor = conn.cursor()
    try:
        # Generate Order No (e.g. YYH_YYYYMMDD_01)
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM orders WHERE date(created_at) = date('now', 'localtime')")
        daily_count = cursor.fetchone()[0] + 1
        order_no = f"YYH_{today_str}_{daily_count:02d}"
        
        cursor.execute('''
            INSERT INTO orders (order_no, customer_name, contact, address, memo)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_no, order.customer_name, order.contact, order.address, order.memo))
        order_id = cursor.lastrowid
        
        for item in order.items:
            if item.quantity > 0:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity)
                    VALUES (?, ?, ?)
                ''', (order_id, item.product_id, item.quantity))
                
        conn.commit()
        return {"status": "success", "order_id": order_id, "order_no": order_no}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/admin/orders")
async def get_orders(status: str = 'pending'):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, order_no, customer_name, contact, address, status, created_at 
        FROM orders 
        WHERE status = ? 
        ORDER BY created_at DESC
        LIMIT 100
    ''', (status,))
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders

class ExportRequest(BaseModel):
    mall_name: str

@app.post("/api/admin/export")
async def export_and_send(req: ExportRequest):
    try:
        result = export_orders_to_excel_and_email(req.mall_name)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class OrderUpdate(BaseModel):
    customer_name: str
    contact: str
    address: str

@app.put("/api/admin/orders/{order_id}")
async def update_order(order_id: int, order: OrderUpdate):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders SET customer_name = ?, contact = ?, address = ? WHERE id = ?
    ''', (order.customer_name, order.contact, order.address, order_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/admin/orders/{order_id}")
async def delete_order(order_id: int):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

class SettingsModel(BaseModel):
    sender_name: str
    sender_email: str
    sender_password: str
    receiver_name: str
    receiver_email: str
    cc_name: str
    cc_email: str

@app.get("/api/admin/settings")
async def get_settings():
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings WHERE id = 1")
    row = dict(cursor.fetchone())
    conn.close()
    return row

@app.post("/api/admin/settings")
async def update_settings(s: SettingsModel):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE settings SET
            sender_name=?, sender_email=?, sender_password=?,
            receiver_name=?, receiver_email=?, cc_name=?, cc_email=?
        WHERE id = 1
    ''', (s.sender_name, s.sender_email, s.sender_password, s.receiver_name, s.receiver_email, s.cc_name, s.cc_email))
    conn.commit()
    conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
