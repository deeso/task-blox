from task_blox.network.elksubmitjson import ElkSubmitJson
from task_blox.os.dirchecker import DirChecker
from task_blox.os.rmfiles import RmFiles
from task_blox.parse.readjsonfile import ReadJsonFile


TASK_BLOX_MAPPER = {
    ElkSubmitJson.key(): ElkSubmitJson,
    DirChecker.key(): DirChecker,
    RmFiles.key(): RmFiles,
    ReadJsonFile.key(): ReadJsonFile,
}
