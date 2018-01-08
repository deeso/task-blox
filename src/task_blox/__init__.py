from network.elksubmitjson import ElkSubmitJson
from os.dirchecker import DirChecker
from os.rmfiles import RmFiles
from parse.readjsonfile import ReadJsonFile


TASK_BLOX_MAPPER = {
    ElkSubmitJson.key(): ElkSubmitJson,
    DirChecker.key(): DirChecker,
    RmFiles.key(): RmFiles,
    ReadJsonFile.key(): ReadJsonFile,
}
