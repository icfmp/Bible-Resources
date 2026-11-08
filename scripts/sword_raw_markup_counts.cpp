// Read the exact compiled SWORD raw per-verse entry WITHOUT any display filters.
// Output numeric counts and original requested verse ID only; never Bible text.
// Build against same experimental HEAD SWORD as the module under audit.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>
#include <map>

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    sword::SWMgr manager;
    sword::SWModule *mod=manager.getModule(argv[1]);
    if (!mod) return 3;
    std::ifstream refs(argv[2]);
    if (!refs) return 4;
    const std::regex tags("<([A-Za-z][A-Za-z0-9]*)\\b");
    std::string ref;
    unsigned long total=0;
    while (std::getline(refs,ref)) {
        if (ref.empty() || ref.size()>120 ||
                ref.find('\t')!=std::string::npos) return 5;
        if (mod->setKey(ref.c_str())) return 6;
        const char *original=mod->getRawEntry();
        if (!original) return 7;
        const std::string text(original);
        std::map<std::string,unsigned> counts;
        for (auto it=std::sregex_iterator(text.begin(),text.end(),tags);
                 it!=std::sregex_iterator(); ++it) {
            ++counts[(*it)[1].str()];
        }
        std::cout << ref << '\t' << counts["w"] << '\t'
                  << counts["note"] << '\t' << counts["reference"] << '\t'
                  << counts["l"] << '\t' << counts["q"] << '\n';
        ++total;
    }
    if (!refs.eof() || total==0) return 8;
    return std::cout.good() ? 0 : 9;
}
