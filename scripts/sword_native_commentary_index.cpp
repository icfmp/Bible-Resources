// Read-only native stock-SWORD commentary occupancy inventory.
// No text, annotations, quotations or raw SWORD bytes printed.
// This observes *occupied VerseKey slots*, NOT authentic authorial
// commentary entries or the editorial start/end of range comments.
// Usage: SWORD_PATH=/isolated/moduleroot ./commentary-index ModuleId
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <sword/swversion.h>
#include <iostream>
#include <regex>
#include <string>

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::string moduleId(argv[1]);
    if (!std::regex_match(moduleId, std::regex("[A-Za-z][A-Za-z0-9_]{0,79}")))
        return 2;
    sword::SWMgr manager;
    sword::SWModule* module = manager.getModule(moduleId.c_str());
    if (!module) return 3;
    const auto* original = dynamic_cast<const sword::VerseKey*>(module->getKey());
    if (!original) return 4;
    const char* drv = module->getConfigEntry("ModDrv");
    const std::string driver = drv ? drv : "";
    if (driver != "RawCom" && driver != "RawCom4"
            && driver != "zCom" && driver != "zCom4") return 5;
    const char* v11nPtr = original->getVersificationSystem();
    const std::string v11n = v11nPtr ? v11nPtr : "";
    const std::string ver = sword::SWVersion::currentVersion.getText();
    if (!std::regex_match(v11n, std::regex("[A-Za-z][A-Za-z0-9]{0,31}"))
            || !std::regex_match(ver, std::regex("[0-9]+\\.[0-9]+\\.[0-9]+")))
        return 6;
    sword::VerseKey key;
    key.setVersificationSystem(v11n.c_str());
    key.setIntros(true);
    key.setAutoNormalize(false);
    key = sword::TOP;
    std::cout << "M\t" << moduleId << '\t' << v11n
              << '\t' << ver << '\t' << driver << '\n';
    const std::regex numbered("[1-4]?[A-Za-z][A-Za-z0-9]*\\.[1-9][0-9]*\\.[1-9][0-9]*");
    const std::regex introduction("[1-4]?[A-Za-z][A-Za-z0-9]*(\\.0\\.0|\\.[1-9][0-9]*\\.0)?");
    unsigned long visited = 0, numberedCount = 0, introCount = 0, topCount = 0;
    while (!key.popError()) {
        if (++visited > 300000) return 7;
        if (module->hasEntry(&key)) {
            std::string ref = key.getOSISRef();
            if (ref.empty() && key.getChapter() == 0 && key.getVerse() == 0) {
                std::cout << "U\tTOP" << '\n';
                ++topCount;
            } else if (key.getChapter() == 0 || key.getVerse() == 0) {
                if (!std::regex_match(ref, introduction)) return 8;
                std::cout << "I\t" << ref << '\n';
                ++introCount;
            } else {
                if (!std::regex_match(ref, numbered)) return 9;
                std::cout << "K\t" << ref << '\n';
                ++numberedCount;
            }
        }
        key++;
    }
    if (numberedCount == 0) return 10;
    std::cout << "S\t" << visited << '\t' << numberedCount
              << '\t' << introCount << '\t' << topCount << '\n';
    return 0;
}
