// Test-only proof of SWORD's existing zCom::linkEntry native index behavior.
// Runs ONLY against the invented synthetic LinkProof module in temporary CI;
// never against BRMHCC, MHCC, a user installation, or any real authorial data.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <iostream>
#include <string>

int main() {
    sword::SWMgr mgr;
    sword::SWModule* module = mgr.getModule("LinkProof");
    if (!module || std::string(module->getConfigEntry("ModDrv") ?
        module->getConfigEntry("ModDrv") : "") != "zCom") return 2;
    if (!module->isWritable()) {
        // Ordinary module loading in released libSWORD may intentionally
        // open zCom indexes read-only. Report a non-buildable capability,
        // NEVER bypass the guard or modify the index binary manually.
        std::cout << "SYNTHETIC_NATIVE_ZCOM_READ_ONLY" << std::endl;
        return 0;
    }
    sword::VerseKey master;
    sword::VerseKey target;
    master.setVersificationSystem("KJV");
    target.setVersificationSystem("KJV");
    master.setAutoNormalize(false);
    target.setAutoNormalize(false);
    master.setText("Gen.1.9");
    target.setText("Gen.1.10");
    if (master.getOSISRef() != std::string("Gen.1.9") ||
        target.getOSISRef() != std::string("Gen.1.10")) return 4;
    if (!module->hasEntry(&master) || module->hasEntry(&target)) return 5;
    if (module->setKey(&target)) return 6;
    module->linkEntry(&master);
    module->flush();
    if (!module->hasEntry(&target)) return 7;
    if (!module->isLinked(&master, &target)) return 8;
    std::cout << "SYNTHETIC_NATIVE_ZCOM_LINK_APPLIED" << std::endl;
    return 0;
}
