# 使用windows monitor API控制显示器参数

from ctypes import windll, byref, Structure, WinError, POINTER, WINFUNCTYPE
from ctypes.wintypes import BOOL, HMONITOR, HDC, RECT, LPARAM, DWORD, BYTE, WCHAR, HANDLE

_MONITORENUMPROC = WINFUNCTYPE(BOOL, HMONITOR, HDC, POINTER(RECT), LPARAM)


class _PHYSICAL_MONITOR(Structure):
    _fields_ = [('handle', HANDLE),
                ('description', WCHAR * 128)]


def _iter_physical_monitors(close_handles=True):
    """Iterates physical monitors.

    The handles are closed automatically whenever the iterator is advanced.
    This means that the iterator should always be fully exhausted!

    If you want to keep handles e.g. because you need to store all of them and
    use them later, set `close_handles` to False and close them manually."""

    def callback(hmonitor, hdc, lprect, lparam):
        monitors.append(HMONITOR(hmonitor))
        return True

    monitors = []
    if not windll.user32.EnumDisplayMonitors(None, None, _MONITORENUMPROC(callback), None):
        raise WinError('EnumDisplayMonitors failed')

    for monitor in monitors:
        # Get physical monitor count
        count = DWORD()
        if not windll.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(monitor, byref(count)):
            raise WinError()
        # Get physical monitor handles
        physical_array = (_PHYSICAL_MONITOR * count.value)()
        if not windll.dxva2.GetPhysicalMonitorsFromHMONITOR(monitor, count.value, physical_array):
            raise WinError()
        for physical in physical_array:
            yield physical.handle
            if close_handles:
                if not windll.dxva2.DestroyPhysicalMonitor(physical.handle):
                    raise WinError()


def set_vcp_feature(monitor, code, value):
    """Sends a DDC command to the specified monitor.

    See this link for a list of commands:
    ftp://ftp.cis.nctu.edu.tw/pub/csie/Software/X11/private/VeSaSpEcS/VESA_Document_Center_Monitor_Interface/mccsV3.pdf
    """
    if not windll.dxva2.SetVCPFeature(HANDLE(monitor), BYTE(code), DWORD(value)):
        raise WinError()

valve = [
    (55, 0), #估计值
    (75, 8), #估计值
    (133, 20), # 准确值
    (170, 30),
]

currentValue = None
def setBrightness(bri):
    """输入亮度值，根据阈值设置显示器亮度"""
    global currentValue
    monitorValue = None
    for k,v in valve:
        if bri < k:
            monitorValue = v
            break
    if monitorValue == None:
        monitorValue = valve[len(valve)-1][1]

    if currentValue != monitorValue:
        currentValue = monitorValue
        for handle in _iter_physical_monitors():
            print('Brightness set to: %s' % monitorValue)
            set_vcp_feature(handle, 0x10, monitorValue)