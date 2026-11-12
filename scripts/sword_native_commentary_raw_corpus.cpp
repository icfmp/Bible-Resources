// Full native commentary raw-entry stream, PRIVATE framing only.
// NEVER execute directly in a public CI shell: stdout includes original commentary XML!
// The Python wrapper consumes the binary stream and emits only metadata hashes.
// Uses released libSWORD; does not modify module bytes, source, versification.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
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
    const char* drv = module->getConfigEntry("ModDrv");
    if (!drv || (std::string(drv) != "RawCom" && std::string(drv) != "RawCom4" &&
                 std::string(drv) != "zCom" && std::string(drv) != "zCom4"))
        return 4;
    const auto* originalKey = dynamic_cast<const sword::VerseKey*>(module->getKey());
    if (!originalKey) return 5;
    const char* nativeVersification = originalKey->getVersificationSystem();
    if (!nativeVersification || !std::regex_match(
            std::string(nativeVersification), std::regex("[A-Za-z][A-Za-z0-9]{0,31}")))
        return 6;
    sword::VerseKey current;
    current.setVersificationSystem(nativeVersification);
    current.setIntros(true);
    current.setAutoNormalize(false);
    current = sword::TOP;
    unsigned long all = 0, numbered = 0, intros = 0, anonymous = 0, visited = 0;
    unsigned long long rawTotal = 0;
    const std::regex numeric("[1-4]?[A-Za-z][A-Za-z0-9]*\\.[1-9][0-9]*\\.[1-9][0-9]*");
    const std::regex intro("[1-4]?[A-Za-z][A-Za-z0-9]*(\\.0\\.0|\\.[1-9][0-9]*(\\.0)?)?");
    while (!current.popError()) {
        if (++visited > 300000) return 7;
        if (module->hasEntry(&current)) {
            std::string osisRef = current.getOSISRef();
            std::string type;
            if (osisRef.empty() && current.getChapter() == 0 &&
                current.getVerse() == 0) {
                type = "U";
                osisRef = "TOP:" + std::to_string(++anonymous);
            }
            else if (current.getVerse() == 0 && std::regex_match(osisRef, intro)) {
                type = "I";
                ++intros;
            }
            else if (current.getChapter() > 0 && current.getVerse() > 0 &&
                     std::regex_match(osisRef, numeric)) {
                type = "K";
                ++numbered;
            }
            else {
                // An occupied but unrecognizable native location is NOT discardable.
                return 8;
            }
            // hasEntry(&current) checks the supplied INDEX but does NOT
            // position SWModule::key. getRawEntry() reads the MODULE'S
            // current key. Without this call, every frame can contain the
            // same text even though the enumerated references are distinct!
            // Use the real VerseKey, never a re-parsed/localized text key.
            if (module->setKey(current)) return 16;
            const auto* positioned =
                dynamic_cast<const sword::VerseKey*>(module->getKey());
            if (!positioned ||
                std::string(positioned->getOSISRef()) !=
                    std::string(current.getOSISRef()) ||
                !module->hasEntry(positioned)) return 17;
            const char* entry = module->getRawEntry();
            if (!entry) return 9;
            const std::string bytes(entry);
            if (bytes.size() > 2 * 1024 * 1024) return 10;
            rawTotal += bytes.size();
            if (rawTotal > 512ull * 1024 * 1024) return 11;
            if (++all > 300000) return 12;
            // Single newline-delimited ASCII frame header, followed by EXACT
            // byte_length raw bytes. Raw XML may contain any newlines or tabs.
            std::cout << type << '\t' << osisRef << '\t'
                      << bytes.size() << '\n';
            std::cout.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
            if (!std::cout.good()) return 13;
        }
        current.increment();
    }
    if (!all || !numbered) return 14;
    std::cout << "S\t" << all << '\t' << numbered << '\t' << intros
              << '\t' << anonymous << '\n';
    return std::cout.good() ? 0 : 15;
}
