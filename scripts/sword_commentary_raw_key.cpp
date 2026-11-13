// PRIVATE single-entry SWORD RawCom/zCom observer: stdout owns raw authorial XML.
// Call only through a bounded Python reader; NEVER tee/stdout to CI logs or
// upload original markup, source words, references or title text.
// This tool reads one existing native key without changing or compiling it.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <iostream>
#include <regex>
#include <string>

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    const std::string moduleId(argv[1]);
    const std::string reference(argv[2]);
    if (!std::regex_match(moduleId,
                          std::regex("[A-Za-z][A-Za-z0-9_]{1,39}")) ||
        !std::regex_match(reference,
                          std::regex("[1-4]?[A-Za-z][A-Za-z ]{0,35} [1-9][0-9]{0,2}:[1-9][0-9]{0,2}")))
        return 2;
    sword::SWMgr manager;
    sword::SWModule* module = manager.getModule(moduleId.c_str());
    if (!module) return 3;
    const char* driver = module->getConfigEntry("ModDrv");
    if (!driver || (std::string(driver) != "RawCom" &&
                    std::string(driver) != "RawCom4" &&
                    std::string(driver) != "zCom" &&
                    std::string(driver) != "zCom4"))
        return 4;
    const auto* nativeKey = dynamic_cast<const sword::VerseKey*>(module->getKey());
    if (!nativeKey) return 5;
    const char* versification = nativeKey->getVersificationSystem();
    if (!versification || !std::regex_match(
            std::string(versification),
            std::regex("[A-Za-z][A-Za-z0-9]{0,31}")))
        return 6;
    sword::VerseKey key;
    key.setVersificationSystem(versification);
    key.setAutoNormalize(false);
    key = reference.c_str();
    if (key.popError() || key.getChapter() <= 0 || key.getVerse() <= 0)
        return 7;
    if (module->setKey(key)) return 8;
    const auto* actual = dynamic_cast<const sword::VerseKey*>(module->getKey());
    if (!actual ||
        std::string(actual->getOSISRef()) != std::string(key.getOSISRef()) ||
        !module->hasEntry(actual))
        return 9; // Sparse commentary slot: do not invent a verse or a title.
    const char* entry = module->getRawEntry();
    if (!entry) return 10;
    const std::string bytes(entry);
    if (bytes.empty() || bytes.size() > 256000) return 11;
    std::cout.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    return std::cout.good() ? 0 : 12;
}
