import psutil
import platform
import cpuinfo

try:
    import GPUtil
except ImportError:
    GPUtil = None


def get_system_info():
    cpu = cpuinfo.get_cpu_info().get("brand_raw", "Unknown CPU")

    ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)

    disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "percent_used": usage.percent
            })
        except PermissionError:
            pass

    gpus = []
    if GPUtil:
        for gpu in GPUtil.getGPUs():
            gpus.append({
                "name": gpu.name,
                "vram_gb": round(gpu.memoryTotal / 1024, 2),
                "load_percent": round(gpu.load * 100, 2)
            })

    return {
        "os": platform.platform(),
        "cpu": cpu,
        "ram_gb": ram_gb,
        "disks": disks,
        "gpus": gpus
    }


def analyze_system(info, workload="analytics"):
    recommendations = []

    cpu_name = info["cpu"].lower()
    ram = info["ram_gb"]

    if "fx" in cpu_name or "amd fx" in cpu_name:
        recommendations.append({
            "priority": "High",
            "component": "CPU / Motherboard / RAM platform",
            "recommendation": "Upgrade to a newer Ryzen or Intel platform.",
            "reason": "AMD FX processors are old and can bottleneck Power BI, PyCharm, browsers, and data processing."
        })

    if workload == "analytics":
        if ram < 16:
            recommendations.append({
                "priority": "High",
                "component": "RAM",
                "recommendation": "Upgrade to at least 16 GB RAM.",
                "reason": "Power BI, PyCharm, and browsers need more memory for smooth multitasking."
            })
        elif ram < 32:
            recommendations.append({
                "priority": "Medium",
                "component": "RAM",
                "recommendation": "Upgrade to 32 GB RAM.",
                "reason": "16 GB is usable, but 32 GB is better for analytics, dashboards, Python, and multitasking."
            })

    for disk in info["disks"]:
        if disk["mountpoint"] == "C:\\":
            if disk["total_gb"] < 250:
                recommendations.append({
                    "priority": "High",
                    "component": "SSD",
                    "recommendation": "Upgrade your system drive to at least 500 GB SSD, ideally 1 TB.",
                    "reason": "A small Windows SSD can slow down apps due to limited free space, cache, and temporary files."
                })

            if disk["percent_used"] > 85:
                recommendations.append({
                    "priority": "High",
                    "component": "Storage free space",
                    "recommendation": "Free up space or upgrade your SSD.",
                    "reason": "Windows performs worse when the system drive is almost full."
                })

    if info["gpus"]:
        for gpu in info["gpus"]:
            if gpu["vram_gb"] < 4:
                recommendations.append({
                    "priority": "Low",
                    "component": "GPU",
                    "recommendation": "GPU upgrade is optional unless gaming, video work, or local AI becomes important.",
                    "reason": "Your GPU is less important than CPU, SSD, and RAM for Power BI and Python work."
                })

    return recommendations


def print_report(info, recommendations):
    print("\n=== PC Upgrade Analyzer Report ===\n")

    print(f"OS: {info['os']}")
    print(f"CPU: {info['cpu']}")
    print(f"RAM: {info['ram_gb']} GB")

    print("\nStorage:")
    for disk in info["disks"]:
        print(
            f"- {disk['device']} {disk['mountpoint']} | "
            f"{disk['total_gb']} GB total | "
            f"{disk['free_gb']} GB free | "
            f"{disk['percent_used']}% used"
        )

    print("\nGPU:")
    if info["gpus"]:
        for gpu in info["gpus"]:
            print(f"- {gpu['name']} | {gpu['vram_gb']} GB VRAM")
    else:
        print("- No GPU detected or GPUtil not available.")

    print("\nRecommendations:")
    for rec in recommendations:
        print(f"\n[{rec['priority']}] {rec['component']}")
        print(f"Recommendation: {rec['recommendation']}")
        print(f"Reason: {rec['reason']}")


if __name__ == "__main__":
    system_info = get_system_info()
    upgrade_recommendations = analyze_system(system_info, workload="analytics")
    print_report(system_info, upgrade_recommendations)
