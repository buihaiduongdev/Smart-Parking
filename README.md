# Car Simulation: Smart-Parking

Dự án hoạt động dựa trên Pygame để điều khiển một chiếc xe tự động di chuyển trên bản đồ (được tải từ file TMX), tránh các chướng ngại vật tĩnh và động (người đi bộ). Được thiết kế để chạy và so sánh hiệu suất của các thuật toán tìm đường khác nhau trong môi trường mô phỏng.

## Tính năng chính

*   **Tải bản đồ TMX:** Tải và hiển thị bản đồ từ định dạng TMX bằng `pytmx`.
*   **Mô phỏng Xe:**
    *   Điều khiển xe di chuyển theo đường đi được tính toán.
    *   Mô phỏng vật lý cơ bản (tốc độ tối đa, giảm tốc khi vào cua).
    *   Tự động tính toán lại đường đi nếu bị kẹt hoặc có yêu cầu.
*   **Chướng ngại vật Động (Người đi bộ):**
    *   Spawn ngẫu nhiên người đi bộ di chuyển theo các đường đi được định nghĩa trước trong bản đồ TMX.
    *   Số lượng người đi bộ và tần suất spawn có thể cấu hình.
    *   Xe cần tránh va chạm với người đi bộ.
*   **So sánh Thuật toán Tìm đường:**
    *   Hỗ trợ chạy nhiều thuật toán tìm đường khác nhau
    *   Chạy nhiều lượt cho mỗi thuật toán để thu thập dữ liệu thống kê.
*   **Cấu hình Linh hoạt:**
    *   Sử dụng file `config.json` để thiết lập các tham số mô phỏng (thuật toán, số lượt chạy, tốc độ, chế độ headless, giới hạn thời gian, v.v.).
*   **Phát hiện Va chạm:** Kiểm tra va chạm giữa xe và các đường biên, chướng ngại vật tĩnh (từ bản đồ TMX), và người đi bộ.
*   **Thu thập và Lưu trữ Kết quả:**
    *   Ghi lại trạng thái kết thúc của mỗi lượt chạy (thành công, va chạm, hết giờ, lỗi tìm đường).
    *   Tính toán các chỉ số hiệu suất (thời gian hoàn thành trung bình, độ dài đường đi trung bình, tỷ lệ thành công, tỷ lệ va chạm, v.v.).
    *   Lưu kết quả tổng hợp vào file JSON.
## Cài đặt

1.  **Clone repository (nếu có):**
    ```bash
    git clone https://github.com/buihaiduongdev/Smart-Parking
    cd Smart-Parking
    ```

2.  **Cài đặt các thư viện Python cần thiết:**
    ```bash
    pip install pygame pytmx numpy
    ```

## Cấu hình (`config.json`)

Tạo file `config.json` trong cùng thư mục với `main.py` với nội dung tương tự như sau, điều chỉnh các giá trị theo nhu cầu:

```json
{
  "algorithms_to_run": ["a_star", "bfs"], // Danh sách các thuật toán để chạy (tên phải khớp với hàm trong pathfinding_algorithms.py)
  "num_runs_per_algorithm": 10,          // Số lần chạy mô phỏng cho mỗi thuật toán
  "simulation_speed_factor": 1.5,        // Hệ số nhân tốc độ mô phỏng (1.0 là bình thường)
  "run_headless": false,                 // true: Chạy không hiển thị cửa sổ; false: Hiển thị cửa sổ Pygame
  "max_run_time_ms": 30000,              // Thời gian tối đa (ms) cho một lượt chạy trước khi bị tính là timeout
  "results_output_file": "simulation_results.json", // Tên file lưu kết quả
  "max_pedestrians": 8,                  // Số lượng người đi bộ tối đa trên bản đồ cùng lúc
  "min_pedestrian_spawn_interval_ms": 5000, // Thời gian chờ tối thiểu (ms) giữa các lần spawn người đi bộ
  "max_pedestrian_spawn_interval_ms": 10000,// Thời gian chờ tối đa (ms) giữa các lần spawn người đi bộ
  "pedestrian_speed": 1.2                 // Tốc độ cơ bản của người đi bộ (sẽ được nhân với simulation_speed_factor)
}
```

## Nguồn tham khảo UI
https://github.com/MindaugasUlskis/Python-Parking-Game-Pygame-
