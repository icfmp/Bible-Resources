// Stable SWORD unfiltered verse markers, no Scripture emitted.
// Unlike the older raw counter, distinguish OSIS <l sID> from <l eID>;
// they are ONE logical source poetry line represented by TWO milestones.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>
#include <map>

int main(int argc,char **argv) {
    if (argc!=3) return 2;
    sword::SWMgr manager;
    sword::SWModule *module=manager.getModule(argv[1]);
    if (!module) return 3;
    std::ifstream refs(argv[2]);
    if (!refs) return 4;
    const std::regex tags("<([A-Za-z][A-Za-z0-9]*)\\b([^>]*)>");
    const std::regex has_sid("\\bsID\\s*=");
    const std::regex has_eid("\\beID\\s*=");
    std::string ref;
    unsigned long total=0;
    while (std::getline(refs,ref)) {
        if (ref.empty()||ref.size()>120||ref.find('\t')!=std::string::npos)
            return 5;
        if (module->setKey(ref.c_str())) return 6;
        const char *raw=module->getRawEntry();
        if (!raw) return 7;
        const std::string xml(raw);
        std::map<std::string,unsigned> counts;
        unsigned line_starts=0,line_ends=0;
        for (auto it=std::sregex_iterator(xml.begin(),xml.end(),tags);
             it!=std::sregex_iterator();++it) {
            const std::string name=(*it)[1].str();
            ++counts[name];
            if (name=="l") {
                const std::string attributes=(*it)[2].str();
                const bool sid=std::regex_search(attributes,has_sid);
                const bool eid=std::regex_search(attributes,has_eid);
                if (sid&&eid) return 8;
                if (eid) ++line_ends;
                else ++line_starts;  // sID or ordinary/selfclosing source line
            }
        }
        std::cout<<ref<<'\t'<<counts["w"]<<'\t'
                 <<counts["note"]<<'\t'<<counts["reference"]<<'\t'
                 <<line_starts<<'\t'<<line_ends<<'\t'
                 <<counts["q"]<<'\n';
        ++total;
    }
    if (!refs.eof()||total==0) return 9;
    return std::cout.good()?0:10;
}
