import customtkinter as ctk
from pcm_dashboard.view.dashboard import PCMDashboard

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    app = PCMDashboard()
    app.mainloop()

if __name__ == "__main__":
    main()