import customtkinter as ctk
from collections import OrderedDict

# ------------------------------------------------------------
# БАЗА ДАННЫХ СТАТИСТИК (без плоских значений)
# ------------------------------------------------------------
STATS_DB = {
    "Крит. урон":           {"avg": 6.6,   "max": 7.77},
    "Шанс крит. попадания": {"avg": 3.3,   "max": 3.89},
    "Сила атаки %": {"avg": 4.975, "max": 5.83},
    "Защита %":    {"avg": 6.2,   "max": 7.29},
    "HP %":        {"avg": 4.975, "max": 5.83},
    "Мастерство стихий":    {"avg": 19.75, "max": 23},
    "Восст. энергии":       {"avg": 5.5,   "max": 6.48},
}
STAT_NAMES = list(STATS_DB.keys())
PRIORITY_STAT_NAMES = [""] + STAT_NAMES
MAIN_STAT_NAMES = STAT_NAMES + ["Другое"]

class ArtifactApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Калькулятор артефактов 2.0")
        self.geometry("1100x750")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.priority_combos = []
        self.value_entries = []
        self.main_stat_combo = None
        self.create_widgets()
        self.calculate()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        left_frame = ctk.CTkFrame(main_frame, width=450)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 20))

        ctk.CTkLabel(left_frame, text="Приоритет и значения доп. статов", font=("Segoe UI", 18, "bold")).pack(pady=(0, 15))

        for i in range(4):
            row_frame = ctk.CTkFrame(left_frame)
            row_frame.pack(fill="x", pady=5)

            num_label = ctk.CTkLabel(row_frame, text=f"{i+1}.", font=("Segoe UI", 14), width=30)
            num_label.pack(side="left", padx=(0, 5))

            combo = ctk.CTkComboBox(row_frame, values=PRIORITY_STAT_NAMES, width=180, font=("Segoe UI", 13),
                                    command=self.on_change)
            combo.pack(side="left", padx=(0, 10))
            combo.set("")
            self.priority_combos.append(combo)

            entry = ctk.CTkEntry(row_frame, width=100, font=("Segoe UI", 14), justify="center")
            entry.pack(side="left")
            entry.bind("<KeyRelease>", self.on_change)
            entry.bind("<FocusOut>", self.on_change)
            self.value_entries.append(entry)

        ctk.CTkFrame(left_frame, height=2, fg_color="gray").pack(fill="x", pady=15)

        ctk.CTkLabel(left_frame, text="Верхний (основной) стат артефакта", font=("Segoe UI", 16)).pack(pady=(0, 10))
        self.main_stat_combo = ctk.CTkComboBox(left_frame, values=MAIN_STAT_NAMES, width=250, font=("Segoe UI", 14),
                                               command=self.on_change)
        self.main_stat_combo.pack(pady=(0, 10))
        self.main_stat_combo.set("Другое")

        reset_btn = ctk.CTkButton(left_frame, text="Сбросить всё", command=self.reset,
                                  font=("Segoe UI", 13), fg_color="#555", hover_color="#777")
        reset_btn.pack(pady=(20, 0))

        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_frame, text="Оценка", font=("Segoe UI", 20, "bold")).pack(pady=(30, 0))
        self.result_label = ctk.CTkLabel(right_frame, text="0.0%", font=("Segoe UI", 72, "bold"))
        self.result_label.pack(expand=True, pady=(0, 10))
        self.detail_label = ctk.CTkLabel(right_frame, text="", font=("Segoe UI", 14))
        self.detail_label.pack(pady=(0, 20))
        self.info_label = ctk.CTkLabel(right_frame, text="", font=("Segoe UI", 12), text_color="orange")
        self.info_label.pack(pady=(10, 0))

    def on_change(self, _=None):
        self.calculate()

    def calculate(self):
        # 1. Сбор введённых значений (сырой балл)
        stats_dict = OrderedDict()
        for i, combo in enumerate(self.priority_combos):
            stat = combo.get()
            if not stat:
                continue
            val_str = self.value_entries[i].get().strip().replace(',', '.')
            if val_str:
                try:
                    val = float(val_str)
                    stats_dict[stat] = val
                except ValueError:
                    pass  # игнорируем ошибочный ввод

        # 2. Список всех приоритетных стат (из комбобоксов, даже без значений)
        all_priority_stats = [combo.get() for combo in self.priority_combos if combo.get()]

        # 3. Веса для стат (по позиции в приоритете)
        priority_weights = {}
        for i, combo in enumerate(self.priority_combos):
            stat = combo.get()
            if stat:
                priority_weights[stat] = 2 if i < 2 else 1

        # 4. Условный максимум (на основе all_priority_stats)
        main_stat = self.main_stat_combo.get()
        # Доступные статы для максимума – все приоритетные, кроме тех, что совпадают с верхним статом
        available_stats = all_priority_stats.copy()
        if main_stat != "Другое" and main_stat in available_stats:
            available_stats.remove(main_stat)

        if not available_stats:
            max_score = 0.0
        else:
            # Выбираем лучшую стату для проков (по коэффициенту max/avg * вес)
            best_coeff = -1
            best_stat = None
            for stat in available_stats:
                if stat in STATS_DB and stat in priority_weights:
                    coeff = (STATS_DB[stat]["max"] / STATS_DB[stat]["avg"]) * priority_weights[stat]
                    if coeff > best_coeff:
                        best_coeff = coeff
                        best_stat = stat

            if best_stat is None:
                max_score = 0.0
            else:
                max_score = 0.0
                # Суммируем вклады всех доступных стат, для лучшей добавляем 5 проков
                for stat in available_stats:
                    if stat not in STATS_DB or stat not in priority_weights:
                        continue
                    max_val = STATS_DB[stat]["max"]
                    avg = STATS_DB[stat]["avg"]
                    w = priority_weights[stat]
                    proks = 5 if stat == best_stat else 0
                    max_score += (max_val / avg) * w * (1 + proks)

        # 5. Сырой балл (только по статам, доступным для проков)
        # Фильтруем stats_dict, оставляя только те статы, которые есть в available_stats
        filtered_stats = {stat: value for stat, value in stats_dict.items() if stat in available_stats}
        raw_score = 0.0
        for stat, value in filtered_stats.items():
            if stat in STATS_DB and stat in priority_weights:
                avg = STATS_DB[stat]["avg"]
                w = priority_weights[stat]
                raw_score += (value / avg) * w

        # 6. Оценка в процентах
        if max_score == 0:
            percent = 0.0
        else:
            percent = (raw_score / max_score) * 100
        percent = round(percent, 1)

        # 7. Цвет и вывод
        if percent < 20:
            color = "#FF4444"
        elif percent < 40:
            color = "#FF8C00"
        elif percent < 60:
            color = "#FFD700"
        elif percent < 80:
            color = "#44CC44"
        else:
            color = "#4488FF"

        self.result_label.configure(text=f"{percent}%", text_color=color)
        self.detail_label.configure(text=f"Сырой балл: {raw_score:.2f}  |  Условный максимум: {max_score:.2f}")

        # Информация об ограничении
        if main_stat != "Другое" and main_stat in all_priority_stats:
            self.info_label.configure(text=f"* Верхний стат '{main_stat}' исключён из возможных проков")
        else:
            self.info_label.configure(text="")

    def reset(self):
        for combo in self.priority_combos:
            combo.set("")
        for entry in self.value_entries:
            entry.delete(0, "end")
        self.main_stat_combo.set("Другое")
        self.calculate()

if __name__ == "__main__":
    app = ArtifactApp()
    app.mainloop()