// Private native SWORD unfiltered raw-entry probe.
// stdout is the original raw SWORD content (NOT a public diagnostic).
// Only invoke from a parent that captures stdout in memory, NEVER as a shell
// command directly on CI log output. Caller produces text-free evidence only.
// Built against released stock libsword; supports RawText and zText.
// This is neither a writer nor a verse-remapping tool.
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
    if (!std::regex_match(moduleId, std::regex("[A-Za-z][A-Za-z0-9_]{0,79}")) ||
        !std::regex_match(reference,
            std::regex("[1-4]?[A-Za-z][A-Za-z0-9]*\\.[1-9][0-9]*\\.[1-9][0-9]*")))
        return 2;
    sword::SWMgr manager;
    sword::SWModule* module = manager.getModule(moduleId.c_str());
    if (!module) return 3;
    auto* verseKey = dynamic_cast<sword::VerseKey*>(module->getKey());
    if (!verseKey) return 4;
    const char* driver = module->getConfigEntry("ModDrv");
    if (!driver || (std::string(driver) != "RawText" &&
                    std::string(driver) != "zText")) return 5;
    verseKey->setAutoNormalize(false);
    verseKey->setIntros(false);
    *verseKey = reference.c_str();
    if (verseKey->popError() ||
        std::string(verseKey->getOSISRef()) != reference ||
        !module->hasEntry(verseKey))
        return 6;  // Unknown or re-addressed key: never inspect substitute.
    const char* raw = module->getRawEntry();
    if (!raw) return 7;
    const std::string text(raw);
    if (text.size() > 2 * 1024 * 1024) return 8;
    std::cout.write(text.data(), static_cast<std::streamsize>(text.size()));
    return std::cout.good() ? 0 : 9;
}
