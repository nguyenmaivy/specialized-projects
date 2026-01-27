# Frontend Development - Next.js & TypeScript

## Tổng quan

Frontend của dự án sử dụng **Next.js 16** (React framework) với **TypeScript** và **Tailwind CSS** để xây dựng giao diện hiện đại, responsive và type-safe.

---

## 📚 Kiến thức cần học

### 1. HTML & CSS Basics
**Thời gian học**: 1-2 tuần

#### HTML:
- **Elements**: `<div>`, `<p>`, `<h1>`, `<button>`, `<input>`
- **Attributes**: `class`, `id`, `style`, `onClick`
- **Semantic HTML**: `<header>`, `<main>`, `<section>`, `<article>`

#### CSS:
- **Selectors**: `.class`, `#id`, `element`
- **Box Model**: margin, padding, border
- **Flexbox**: `display: flex`, `justify-content`, `align-items`
- **Grid**: `display: grid`, `grid-template-columns`
- **Responsive Design**: Media queries

#### Tài liệu học:
- [MDN HTML](https://developer.mozilla.org/en-US/docs/Web/HTML)
- [MDN CSS](https://developer.mozilla.org/en-US/docs/Web/CSS)
- [CSS Tricks - Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)

---

### 2. JavaScript/TypeScript
**Thời gian học**: 3-4 tuần

#### JavaScript Fundamentals:
- **Variables**: `let`, `const`, `var`
- **Data Types**: string, number, boolean, array, object
- **Functions**: Arrow functions `() => {}`
- **Array Methods**: `.map()`, `.filter()`, `.reduce()`
- **Async/Await**: Xử lý API calls
- **Destructuring**: `const { name, age } = person`
- **Spread Operator**: `...array`, `...object`

#### TypeScript Additions:
- **Type Annotations**: `name: string`, `age: number`
- **Interfaces**: Định nghĩa cấu trúc object
- **Generics**: `Array<string>`, `Promise<Data>`
- **Type Safety**: Catch errors trước khi chạy

#### Code ví dụ:
```typescript
// Interface definition
interface KPIData {
    total_sales: number;
    total_profit: number;
    total_orders: number;
    avg_discount: number;
}

// Function with types
const fetchKPIs = async (filters: Filters): Promise<KPIData> => {
    const response = await axios.get<KPIData>('/api/kpis', { params: filters });
    return response.data;
};

// Array methods
const categories = data.map(item => item.Category);
const highSales = data.filter(item => item.Sales > 1000);
```

#### Tài liệu học:
- [JavaScript.info](https://javascript.info/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [TypeScript for JavaScript Programmers](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html)

---

### 3. React Fundamentals
**Thời gian học**: 2-3 tuần

#### Core Concepts:
- **Components**: Function components
- **JSX**: HTML-like syntax trong JavaScript
- **Props**: Truyền data giữa components
- **State**: `useState()` hook
- **Effects**: `useEffect()` hook
- **Event Handling**: `onClick`, `onChange`
- **Conditional Rendering**: `{condition && <Component />}`
- **Lists**: `.map()` để render arrays

#### Code ví dụ:
```typescript
import { useState, useEffect } from 'react';

export default function Dashboard() {
    // State management
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<KPIData | null>(null);

    // Side effects (API calls)
    useEffect(() => {
        fetchKPIs({})
            .then(result => {
                setData(result);
                setLoading(false);
            })
            .catch(err => console.error(err));
    }, []); // Empty array = run once on mount

    // Conditional rendering
    if (loading) return <div>Loading...</div>;
    if (!data) return <div>No data</div>;

    // Render UI
    return (
        <div>
            <h1>Total Sales: ${data.total_sales}</h1>
        </div>
    );
}
```

#### Tài liệu học:
- [React Official Tutorial](https://react.dev/learn)
- [React Hooks](https://react.dev/reference/react)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

---

### 4. Next.js Framework
**Thời gian học**: 1 tuần

#### Key Features:
- **App Router**: File-based routing (Next.js 13+)
- **Server Components**: Default trong App Router
- **Client Components**: `"use client"` directive
- **Layouts**: Shared UI across pages
- **Routing**: `app/page.tsx`, `app/customers/page.tsx`
- **Link Component**: Navigation giữa pages

#### File Structure:
```
app/
├── layout.tsx          # Root layout (wraps all pages)
├── page.tsx            # Home page (/)
└── customers/
    └── page.tsx        # Customers page (/customers)
```

#### Code ví dụ:
```typescript
// app/page.tsx - Home page
import Link from 'next/link';

export default function Home() {
    return (
        <main>
            <h1>Dashboard</h1>
            <Link href="/customers">
                View Customers
            </Link>
        </main>
    );
}

// app/customers/page.tsx - Customers page
"use client"; // Client component for interactivity

export default function CustomersPage() {
    return <div>Customer Insights</div>;
}
```

#### Tài liệu học:
- [Next.js Documentation](https://nextjs.org/docs)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Next.js Learn Course](https://nextjs.org/learn)

---

### 5. Tailwind CSS
**Thời gian học**: 3-5 ngày

#### Utility-First CSS:
Thay vì viết CSS riêng, dùng classes có sẵn:

```html
<!-- Traditional CSS -->
<div class="card">
    <h1 class="title">Hello</h1>
</div>

<!-- Tailwind CSS -->
<div class="bg-white p-6 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold text-gray-900">Hello</h1>
</div>
```

#### Common Classes:
- **Spacing**: `p-4` (padding), `m-2` (margin), `gap-4`
- **Colors**: `bg-blue-500`, `text-gray-700`, `border-red-300`
- **Typography**: `text-xl`, `font-bold`, `text-center`
- **Layout**: `flex`, `grid`, `items-center`, `justify-between`
- **Responsive**: `md:flex`, `lg:grid-cols-3`

#### Tài liệu học:
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Tailwind CSS Cheat Sheet](https://nerdcave.com/tailwind-cheat-sheet)

---

### 6. Chart.js - Data Visualization
**Thời gian học**: 2-3 ngày

#### Chart Types trong dự án:
- **Line Chart**: Sales trend over time
- **Bar Chart**: Sales by category
- **Pie Chart**: Regional distribution, Customer segments
- **Bubble Chart**: RFM analysis

#### Code ví dụ:
```typescript
import { Line, Pie, Bubble } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement } from 'chart.js';

// Register components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement);

// Prepare data
const data = {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{
        label: 'Sales',
        data: [1200, 1900, 1500],
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)'
    }]
};

// Render chart
<Line data={data} options={{ responsive: true }} />
```

#### Tài liệu học:
- [Chart.js Documentation](https://www.chartjs.org/docs/latest/)
- [react-chartjs-2 Documentation](https://react-chartjs-2.js.org/)

---

## 🎯 Lộ trình học Frontend

### Tuần 1-2: HTML/CSS Basics
- Tạo trang web tĩnh đơn giản
- Thực hành Flexbox và Grid
- Làm responsive design

### Tuần 3-5: JavaScript/TypeScript
- Học ES6+ features
- Thực hành array methods
- Làm bài tập TypeScript

### Tuần 6-8: React
- Tạo components
- Quản lý state với useState
- Fetch data với useEffect
- Build todo app hoặc weather app

### Tuần 9: Next.js
- Tạo multi-page app
- Học routing
- Deploy lên Vercel

### Tuần 10: Tailwind + Chart.js
- Style components với Tailwind
- Tạo charts với Chart.js
- Hoàn thiện dashboard

---

## 🛠 Tools cần cài đặt

1. **Node.js 18+**: [Download](https://nodejs.org/)
2. **VS Code**: [Download](https://code.visualstudio.com/)
3. **Git**: [Download](https://git-scm.com/)

### VS Code Extensions:
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- TypeScript Vue Plugin (Volar)
- Prettier - Code formatter
- ESLint

---

## 📖 Tài liệu tham khảo

- [Next.js Docs](https://nextjs.org/docs)
- [React Docs](https://react.dev)
- [TypeScript Docs](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Chart.js Docs](https://www.chartjs.org/docs/)

---

## 💡 Tips học tập

1. **Build projects**: Học qua làm, không chỉ xem video
2. **Read documentation**: Docs là nguồn tài liệu tốt nhất
3. **Use DevTools**: Chrome DevTools để debug
4. **Component thinking**: Chia UI thành components nhỏ
5. **TypeScript từ đầu**: Học TypeScript ngay, đừng học JS rồi mới chuyển
6. **Responsive first**: Test trên mobile và desktop
