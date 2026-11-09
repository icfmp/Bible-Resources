// Native stable-SWORD Bible verse-index inventory, independently of source OSIS.
// No Scripture, note content or lexeme is emitted. Build against released
// libSWORD (not HEAD or a custom local versification implementation).
//
// Usage: SWORD_PATH=/isolated/payload ./sword-native-index ModuleId
// stdout records:
// M<TAB>module-id<TAB>native-versification<TAB>libsword-version<TAB>driver
// R<TAB>native-versification<TAB>osis-book<TAB>chapter<TAB>last-registry-verse
// K<TAB>populated-native-osis-book.chapter.verse
// I<TAB>populated-native-verse-zero-intro-reference
// S<TAB>number-of-registry-chapters<TAB>populated-ordinary-verses<TAB>populated-intros
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <sword/swversion.h>
#include <iostream>
#include <regex>
#include <string>

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::string requested(argv[1]);
    if (!std::regex_match(requested, std::regex("[A-Za-z][A-Za-z0-9_]{0,79}")))
        return 2;
    sword::SWMgr mgr;
    sword::SWModule* module = mgr.getModule(requested.c_str());
    if (!module) return 3;
    const auto* moduleKey = dynamic_cast<const sword::VerseKey*>(module->getKey());
    if (!moduleKey) return 4;
    const char* v11nRaw = moduleKey->getVersificationSystem();
    const char* driverRaw = module->getConfigEntry("ModDrv");
    const std::string v11n = v11nRaw ? v11nRaw : "";
    const std::string driver = driverRaw ? driverRaw : "";
    const std::string version = sword::SWVersion::currentVersion.getText();
    if (!std::regex_match(v11n, std::regex("[A-Za-z][A-Za-z0-9]{0,31}"))
        || (driver != "RawText" && driver != "zText")
        || !std::regex_match(version, std::regex("[0-9]+\\.[0-9]+\\.[0-9]+")))
        return 5;

    sword::VerseKey current;
    current.setVersificationSystem(v11n.c_str());
    current.setIntros(true);
    current.setAutoNormalize(false);
    current = sword::TOP;
    std::cout << "M\t" << requested << '\t' << v11n
              << '\t' << version << '\t' << driver << '\n';
    unsigned long registryChapters = 0;
    unsigned long populated = 0;
    unsigned long intros = 0;
    unsigned long scanned = 0;
    std::string lastChapter;
    while (!current.popError()) {
        if (++scanned > 300000) return 6;
        const std::string id = current.getOSISRef();
        const int chapter = current.getChapter();
        const int verse = current.getVerse();
        // libSWORD's TOP iterator sentinel may have no OSISRef at 0:0.
        // Skip it only when no actual module entry is stored there.
        if (id.empty() && chapter == 0 && verse == 0) {
            if (module->hasEntry(&current)) {
                std::cerr << "Nonaddressable populated SWORD TOP introduction" << '\n';
                return 12;
            }
            current.increment();
            continue;
        }
        const std::size_t dot1 = id.find('.');
        const std::size_t dot2 = id.find('.', dot1 == std::string::npos ? 0 : dot1 + 1);
        if (dot1 == std::string::npos || dot2 == std::string::npos
            || id.find('.', dot2 + 1) != std::string::npos) {
            // Only identifiers and numeric metadata, never original text.
            std::cerr << "Unrecognized native key: " << id
                      << " (chapter " << current.getChapter()
                      << ", verse " << current.getVerse() << ")\n";
            return 7;
        }
        const std::string book = id.substr(0, dot1);
        const std::string ch = id.substr(dot1 + 1, dot2 - dot1 - 1);
        if (chapter < 0 || verse < 0) return 8;
        if (chapter > 0 && verse > 0) {
            const int limit = current.getVerseMax();
            if (verse > limit || limit < 1) return 8;
            const std::string chapterKey = book + "." + ch;
            if (chapterKey != lastChapter) {
                if (verse != 1) return 9;
                std::cout << "R\t" << v11n << '\t' << book
                          << '\t' << chapter << '\t' << limit << '\n';
                lastChapter = chapterKey;
                ++registryChapters;
            }
            if (module->hasEntry(&current)) {
                std::cout << "K\t" << id << '\n';
                ++populated;
            }
        }
        else if (verse == 0 && module->hasEntry(&current)) {
            std::cout << "I\t" << id << '\n';
            ++intros;
        }
        current.increment();
    }
    if (!registryChapters || !populated || !std::cout.good()) return 10;
    std::cout << "S\t" << registryChapters << '\t' << populated
              << '\t' << intros << '\n';
    return std::cout.good() ? 0 : 11;
}
