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
    if (!module->isWritable()) return 3;
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
    std::cout << "SWORD synthetic only: native zCom linkEntry API completed" << std::endl;
    return 0;
}
