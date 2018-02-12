from task_blox.network.elksubmitjson import ElkSubmitJson
from task_blox.network.pgsubmitjsonnc import PGSubmitJsonNC
from task_blox.os.dirchecker import DirChecker
from task_blox.os.rmfiles import RmFiles
from task_blox.parse.readjsonfile import ReadJsonFile
from task_blox.parse.jsonupdate import KeyedJsonUpdate


TASK_BLOX_MAPPER = {
    ElkSubmitJson.key(): ElkSubmitJson,
    DirChecker.key(): DirChecker,
    RmFiles.key(): RmFiles,
    ReadJsonFile.key(): ReadJsonFile,
    KeyedJsonUpdate.key(): KeyedJsonUpdate,
    PGSubmitJsonNC.key(): PGSubmitJsonNC,
    'postgressubmitjsonnc': PGSubmitJsonNC,
}
