import streamlit as st
import psutil
import platform
import cpuinfo

try:
    import GPUtil
except ImportError:
    GPUtil = None


st.set_page_config(page_title="PC Upgrade Analyzer", layout="wide")

st.title("PC Upgrade Analyzer")
st.write("Analyze system hardware and get upgrade recommendations.")


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
        except Exception:
            pass

    gpus = []
    if GPUtil:
        try:
            for gpu in GPUtil.getGPUs():
                gpus.append({
                    "name": gpu.name,
                    "vram_gb": round(gpu.memoryTotal / 1024, 2),
                    "load_percent": round(gpu.load * 100, 2)
                })
        except Exception:
            pass

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
        is_system_drive = disk["mountpoint"] in ["C:\\", "/"]

        if is_system_drive and disk["total_gb"] < 250:
            recommendations.append({
                "priority": "High",
                "component": "SSD",
                "recommendation": "Upgrade your system drive to at least 500 GB SSD, ideally 1 TB.",
                "reason": "A small system drive can slow down apps due to limited free space, cache, and temporary files."
            })

        if is_system_drive and disk["percent_used"] > 85:
            recommendations.append({
                "priority": "High",
                "component": "Storage free space",
                "recommendation": "Free up space or upgrade your SSD.",
                "reason": "The system drive performs worse when it is almost full."
            })

    if info["gpus"]:
        for gpu in info["gpus"]:
            if gpu["vram_gb"] < 4:
                recommendations.append({
                    "priority": "Low",
                    "component": "GPU",
                    "recommendation": "GPU upgrade is optional unless gaming, video work, or local AI becomes important.",
                    "reason": "GPU is less important than CPU, SSD, and RAM for Power BI and Python work."
                })

    return recommendations


workload = st.sidebar.selectbox(
    "Select workload",
    ["analytics", "gaming", "general productivity"]
)

system_info = get_system_info()
upgrade_recommendations = analyze_system(system_info, workload=workload)

st.header("System Information")

col1, col2, col3 = st.columns(3)

col1.metric("CPU", system_info["cpu"])
col2.metric("RAM", f"{system_info['ram_gb']} GB")
col3.metric("OS", system_info["os"])

st.subheader("Storage")

if system_info["disks"]:
    st.dataframe(system_info["disks"], use_container_width=True)
else:
    st.warning("No storage information detected.")

st.subheader("GPU")

if system_info["gpus"]:
    st.dataframe(system_info["gpus"], use_container_width=True)
else:
    st.info("No GPU detected or GPUtil is not available.")

st.header("Upgrade Recommendations")

if upgrade_recommendations:
    for rec in upgrade_recommendations:
        if rec["priority"] == "High":
            st.error(f"{rec['priority']} Priority: {rec['component']}")
        elif rec["priority"] == "Medium":
            st.warning(f"{rec['priority']} Priority: {rec['component']}")
        else:
            st.info(f"{rec['priority']} Priority: {rec['component']}")

        st.write(f"**Recommendation:** {rec['recommendation']}")
        st.write(f"**Reason:** {rec['reason']}")
        st.divider()
else:
    st.success("No major upgrade recommendations detected.")