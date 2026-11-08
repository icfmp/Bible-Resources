// Read-only, versioned SWORD canonical verse ceilings.
// Built against the *installed* SWORD library; no text/Bible data is linked,
// read or emitted. Output: registry<TAB>osisBook<TAB>chapter<TAB>verseMax.
#include <sword/versificationmgr.h>
#include <iostream>

int main() {
    auto *manager = sword::VersificationMgr::getSystemVersificationMgr();
    if (!manager) return 2;
    auto systems = manager->getVersificationSystems();
    if (systems.empty()) return 3;
    for (const auto &name : systems) {
        const auto *system = manager->getVersificationSystem(name.c_str());
        if (!system) return 4;
        for (int index = 0; index < system->getBookCount(); ++index) {
            const auto *book = system->getBook(index);
            if (!book || !book->getOSISName()) return 5;
            for (int chapter = 1; chapter <= book->getChapterMax(); ++chapter) {
                const int verse_max = book->getVerseMax(chapter);
                if (verse_max <= 0) return 6;
                std::cout << name.c_str() << '\t' << book->getOSISName()
                          << '\t' << chapter << '\t' << verse_max << '\n';
            }
        }
    }
    return std::cout.good() ? 0 : 7;
}
