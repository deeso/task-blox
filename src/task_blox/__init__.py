from network.elksubmitjson import ElkSubmitJson
from os.dirchecker import DirChecker
from os.rmfiles import RmFiles
from parse.readjsonfile import ReadJsonFile


TASK_BLOX = {
    ElkSubmitJson.name(): ElkSubmitJson,
    DirChecker.name(): DirChecker,
    RmFiles.name(): RmFiles,
    ReadJsonFile.name(): ReadJsonFile,
}
