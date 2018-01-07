from network.elksubmitjson import ElkSubmitJson
from os.dirchecker import DirChecker
from os.rmfiles import RmFiles
from parse.readjsonfile import ReadJsonFile


TASK_BLOX_MAPPER = {
    ElkSubmitJson.name(): ElkSubmitJson,
    DirChecker.name(): DirChecker,
    RmFiles.name(): RmFiles,
    ReadJsonFile.name(): ReadJsonFile,
}
