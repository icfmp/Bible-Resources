// Module-owned complete stable-SWORD text-rendering regression gate.
// Read only; never output copyrighted/authorial content, just counts and keys.
// Fail if displayed plain text includes internal OSIS markup with notes/xrefs Off.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <iostream>
#include <string>
#include <regex>
#include <cstring>

static bool leaked(const std::string& s) {
    // Raw OSIS tags or escaped literals are not biblical text.
    return s.find("<reference") != std::string::npos ||
           s.find("</reference") != std::string::npos ||
           s.find("osisRef=") != std::string::npos ||
           s.find("&lt;reference") != std::string::npos ||
           s.find("<note") != std::string::npos ||
           s.find("</note") != std::string::npos;
}

int main(int argc, char** argv) {
    if (argc != 2 || std::strcmp(argv[1], "BRLSG1910") != 0) return 2;
    sword::SWMgr mgr;
    sword::SWModule* module = mgr.getModule(argv[1]);
    if (!module) { std::cerr << "Module is missing\n"; return 3; }
    const char* driver = module->getConfigEntry("ModDrv");
    if (!driver || std::string(driver) != "zText") return 4;
    const auto* module_key = dynamic_cast<const sword::VerseKey*>(module->getKey());
    if (!module_key) return 5;
    sword::VerseKey key;
    key.setVersificationSystem(module_key->getVersificationSystem());
    key.setIntros(true);
    key.setAutoNormalize(false);
    key = sword::TOP;
    const std::regex numbered("[1-4]?[A-Za-z][A-Za-z0-9]*\\.[1-9][0-9]*\\.[1-9][0-9]*");
    mgr.setGlobalOption("Cross-references", "Off");
    mgr.setGlobalOption("Footnotes", "Off");
    unsigned long total = 0, checked = 0, markup = 0, navigated = 0;
    while (!key.popError()) {
        if (++total > 300000) return 6;
        if (module->hasEntry(&key)) {
            const std::string ref = key.getOSISRef();
            if (std::regex_match(ref, numbered)) {
                if (module->setKey(key)) return 7;
                if (!module->hasEntry(module->getKey())) return 8;
                const std::string displayed = module->stripText();
                if (leaked(displayed)) {
                    ++markup;
                    if (markup <= 20) std::cerr << "Leaked markup at " << ref << "\n";
                }
                ++checked;
                if (ref == "Rom.1.7" || ref == "Rom.1.9" ||
                    ref == "John.1.1" || ref == "Gen.1.1") ++navigated;
            }
        }
        key.increment();
    }
    std::cout << "Native populated verse text checked: " << checked
              << "; leaked OSIS markup: " << markup
              << "; reported exemplar verses checked: " << navigated << "\n";
    if (checked != 31169 || navigated != 4 || markup) return 9;
    // Cross-references=On remains a documented libSWORD stripText limitation;
    // forcing on in this gate would reject immutable note markup, not cure it.
    return 0;
}
