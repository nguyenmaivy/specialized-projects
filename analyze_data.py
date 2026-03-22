"""
Script phân tích dữ liệu SampleSuperstore.csv
Giúp hiểu rõ cấu trúc và chất lượng dữ liệu
"""

import pandas as pd
import sys
import os

# Đường dẫn file dữ liệu
DATA_PATH = "data/SampleSuperstore.csv"

def analyze_data():
    """Phân tích chi tiết bộ dữ liệu"""
    
    print("=" * 80)
    print("PHÂN TÍCH DỮ LIỆU SAMPLE SUPERSTORE")
    print("=" * 80)
    
    # Kiểm tra file tồn tại
    if not os.path.exists(DATA_PATH):
        print(f"❌ Không tìm thấy file: {DATA_PATH}")
        return
    
    # Đọc dữ liệu
    print("\n📂 Đang đọc dữ liệu...")
    df = pd.read_csv(DATA_PATH, encoding='latin-1')
    
    # 1. THÔNG TIN CƠ BẢN
    print("\n" + "=" * 80)
    print("1. THÔNG TIN CƠ BẢN")
    print("=" * 80)
    print(f"📊 Số dòng (records): {len(df):,}")
    print(f"📋 Số cột (columns): {len(df.columns)}")
    print(f"💾 Kích thước file: {os.path.getsize(DATA_PATH) / 1024:.2f} KB")
    
    # 2. CẤU TRÚC DỮ LIỆU
    print("\n" + "=" * 80)
    print("2. CẤU TRÚC DỮ LIỆU (Các cột có sẵn)")
    print("=" * 80)
    print("\nCác cột trong file:")
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        null_count = df[col].isnull().sum()
        print(f"  {i:2d}. {col:20s} - Kiểu: {str(dtype):10s} - Null: {null_count:4d}")
    
    # 3. MẪU DỮ LIỆU
    print("\n" + "=" * 80)
    print("3. MẪU DỮ LIỆU (5 dòng đầu tiên)")
    print("=" * 80)
    print(df.head().to_string())
    
    # 4. THỐNG KÊ THỜI GIAN
    print("\n" + "=" * 80)
    print("4. PHÂN TÍCH THỜI GIAN")
    print("=" * 80)
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%m/%d/%Y')
    print(f"📅 Ngày đầu tiên: {df['Order Date'].min().strftime('%d/%m/%Y')}")
    print(f"📅 Ngày cuối cùng: {df['Order Date'].max().strftime('%d/%m/%Y')}")
    
    date_range = (df['Order Date'].max() - df['Order Date'].min()).days
    print(f"⏱️  Khoảng thời gian: {date_range} ngày ({date_range/365:.1f} năm)")
    print(f"📆 Số ngày có dữ liệu: {df['Order Date'].nunique()} ngày")
    
    # Kiểm tra đủ dữ liệu cho Prophet
    if df['Order Date'].nunique() >= 50:
        print("✅ ĐỦ dữ liệu cho dự báo Prophet (cần ≥50 ngày)")
    else:
        print("❌ CHƯA ĐỦ dữ liệu cho dự báo Prophet (cần ≥50 ngày)")
    
    # 5. THỐNG KÊ KHÁCH HÀNG
    print("\n" + "=" * 80)
    print("5. PHÂN TÍCH KHÁCH HÀNG")
    print("=" * 80)
    num_customers = df['Customer ID'].nunique()
    print(f"👥 Số khách hàng: {num_customers:,}")
    print(f"📦 Số đơn hàng: {df['Order ID'].nunique():,}")
    print(f"📊 Trung bình đơn/khách: {df['Order ID'].nunique() / num_customers:.2f}")
    
    # Kiểm tra đủ dữ liệu cho phân khúc
    if num_customers >= 100:
        print("✅ ĐỦ khách hàng cho phân khúc K-Means (cần ≥100 KH)")
    else:
        print("❌ CHƯA ĐỦ khách hàng cho phân khúc K-Means (cần ≥100 KH)")
    
    # 6. THỐNG KÊ DOANH THU
    print("\n" + "=" * 80)
    print("6. PHÂN TÍCH DOANH THU")
    print("=" * 80)
    print(f"💰 Tổng doanh thu: ${df['Sales'].sum():,.2f}")
    print(f"💵 Tổng lợi nhuận: ${df['Profit'].sum():,.2f}")
    print(f"📈 Tỷ suất lợi nhuận: {df['Profit'].sum() / df['Sales'].sum() * 100:.2f}%")
    print(f"🎯 Doanh thu trung bình/đơn: ${df['Sales'].mean():,.2f}")
    print(f"🔻 Chiết khấu trung bình: {df['Discount'].mean() * 100:.2f}%")
    
    # 7. PHÂN TÍCH THEO DANH MỤC
    print("\n" + "=" * 80)
    print("7. PHÂN TÍCH THEO DANH MỤC")
    print("=" * 80)
    category_sales = df.groupby('Category')['Sales'].sum().sort_values(ascending=False)
    print("\nDoanh thu theo danh mục:")
    for cat, sales in category_sales.items():
        pct = sales / category_sales.sum() * 100
        print(f"  📦 {cat:20s}: ${sales:12,.2f} ({pct:5.2f}%)")
    
    # 8. PHÂN TÍCH THEO KHU VỰC
    print("\n" + "=" * 80)
    print("8. PHÂN TÍCH THEO KHU VỰC")
    print("=" * 80)
    region_sales = df.groupby('Region')['Sales'].sum().sort_values(ascending=False)
    print("\nDoanh thu theo khu vực:")
    for region, sales in region_sales.items():
        pct = sales / region_sales.sum() * 100
        print(f"  🌍 {region:20s}: ${sales:12,.2f} ({pct:5.2f}%)")
    
    # 9. CHẤT LƯỢNG DỮ LIỆU
    print("\n" + "=" * 80)
    print("9. ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU")
    print("=" * 80)
    
    # Kiểm tra giá trị null
    null_counts = df.isnull().sum()
    if null_counts.sum() == 0:
        print("✅ Không có giá trị NULL")
    else:
        print("⚠️  Có giá trị NULL:")
        for col, count in null_counts[null_counts > 0].items():
            print(f"   - {col}: {count} giá trị")
    
    # Kiểm tra giá trị âm
    if (df['Sales'] < 0).any():
        print(f"⚠️  Có {(df['Sales'] < 0).sum()} giá trị Sales âm")
    else:
        print("✅ Không có giá trị Sales âm")
    
    # Kiểm tra trùng lặp
    duplicates = df.duplicated(subset=['Order ID']).sum()
    if duplicates > 0:
        print(f"⚠️  Có {duplicates} đơn hàng trùng lặp")
    else:
        print("✅ Không có đơn hàng trùng lặp")
    
    # 10. KẾT LUẬN
    print("\n" + "=" * 80)
    print("10. KẾT LUẬN & KHUYẾN NGHỊ")
    print("=" * 80)
    
    print("\n✅ DỮ LIỆU HIỆN TẠI:")
    print(f"   - {len(df):,} giao dịch")
    print(f"   - {df['Order Date'].nunique()} ngày có dữ liệu")
    print(f"   - {num_customers:,} khách hàng")
    print(f"   - {df['Order ID'].nunique():,} đơn hàng")
    
    print("\n📊 TÍNH NĂNG CÓ THỂ SỬ DỤNG:")
    features = []
    if df['Order Date'].nunique() >= 50:
        features.append("✅ Dự báo bán hàng (Prophet)")
    else:
        features.append("❌ Dự báo bán hàng (cần thêm dữ liệu)")
    
    if num_customers >= 100:
        features.append("✅ Phân khúc khách hàng (RFM + K-Means)")
    else:
        features.append("❌ Phân khúc khách hàng (cần thêm khách hàng)")
    
    features.append("✅ Dashboard KPI")
    features.append("✅ Biểu đồ xu hướng")
    features.append("✅ Phân tích theo danh mục/khu vực")
    
    for feature in features:
        print(f"   {feature}")
    
    print("\n💡 KHUYẾN NGHỊ:")
    if df['Order Date'].nunique() < 50:
        print("   - Cần thêm dữ liệu (ít nhất 50 ngày) để dự báo chính xác")
    if num_customers < 100:
        print("   - Cần thêm khách hàng (ít nhất 100 KH) để phân khúc hiệu quả")
    if null_counts.sum() > 0:
        print("   - Cần xử lý giá trị NULL trước khi phân tích")
    if (df['Sales'] < 0).any():
        print("   - Cần kiểm tra và xử lý giá trị Sales âm")
    
    if df['Order Date'].nunique() >= 50 and num_customers >= 100 and null_counts.sum() == 0:
        print("   🎉 Dữ liệu ĐẦY ĐỦ và SẴN SÀNG cho tất cả tính năng!")
    
    print("\n" + "=" * 80)
    print("HOÀN THÀNH PHÂN TÍCH!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_data()
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
