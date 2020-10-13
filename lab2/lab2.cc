#include <iostream>
#include <string>
#include <map>
#include <vector>
#include <algorithm>
#include <set>
#include <functional>
#include <iomanip>


#define DEBUG

class Symbol{
    enum class Type{
        TERMINAL,
        NON_TERMINAL
    };

    private:
    Type _type;
    char _c;
    std::vector<std::string> _candidates;

    public:

    Symbol() {
        _c = '\0';
    }

    Symbol(char c){
        _type = Type::TERMINAL;
        _c = c;
    }

    Symbol(const Symbol & s) {
        _type = s._type;
        _c = s._c;
        _candidates = s._candidates;
    }

    void setAsNonTerminal(const std::string &p) {
        _type = Type::NON_TERMINAL;

        auto split = [](const std::string& s, char d) -> auto{
            std::vector<std::string> v;
            auto start = 0U;
            auto end = s.find(d);
            while(end != std::string::npos) {
                v.emplace_back(s.substr(start, end));
                start = end + 1;
                end = s.find(d, start);
            }
            v.emplace_back(s.substr(start, end));
            return v;
        };
        _candidates = split(p, '|');
    }

    auto isTerminal() const{
        return (_type == Type::TERMINAL);
    }

    auto getCandidates() const{
        return _candidates;
    }

    auto getChar() const{
        return _c;
    }

    void print() const{
        std::cout << "Char : " << getChar() << std::endl;
        std::cout << (isTerminal() ? "Terminal" : "Non-Terminal") << std::endl;

        for(size_t i = 0; _candidates.size() && i < _candidates.size() - 1; ++i) {
            std::cout << _candidates[i] << '|';
        }

        if(_candidates.size()) {
            std::cout << _candidates.back();
        }
    }
};


std::map<char, Symbol> symsGen(const std::vector<std::string> & productions) {
    std::map<char, Symbol> smap;
    for(auto && x : productions) {
        auto pos = x.find("->");
        if(pos == std::string::npos) {
            throw std::string("can not find \"->\" in a production : ") + x;
        }

        if(pos != 1) {
            throw std::string("production format error, production : ") + x;
        }

        // process content at the left of "->"
        if(smap.find(x[0]) == smap.end()) {
            Symbol s(x[0]);
            s.setAsNonTerminal(x.substr(pos + 2));
            smap.emplace(x[0], s);
        } else {
            smap[x[0]].setAsNonTerminal(x.substr(pos + 2));
        }

        // process content at the right of "->"
        for(size_t i = pos + 2; i < x.size(); ++i) {
            if(smap.find(x[i]) == smap.end()) {
                if(x[i] == '|') {
                    continue;
                }
                Symbol tmp(x[i]);
                smap[x[i]] = tmp;
            }
        }
    }

    return smap;
}


auto firstfollowSetGen(const std::map<char, Symbol> &smap) {
    std::map<char, std::set<char>> first;
    std::map<char, std::set<char>> follow;
    std::map<char, bool> nullable;

    for(auto && [x,y] : smap) {
        if(y.isTerminal()) {
            std::set<char> tmp;
            tmp.insert(x);
            first[x] = tmp;
        } else {
            first[x] = {};
        }
        follow[x] = {};
        nullable[x] = false;
    }

    nullable['?'] = true;

    auto myintersec = [](const auto &s1, const auto &s2) {
        std::remove_cvref_t<decltype(s1)> tmp;
        std::insert_iterator ins{tmp, tmp.begin()};
        std::set_intersection(s1.cbegin(), s1.cend(), s2.cbegin(), s2.cend(), ins);
        return tmp;
    };

    auto myunion = [](const auto& s1, const auto &s2) {
        std::remove_cvref_t<decltype(s1)> tmp;
        std::insert_iterator ins{tmp, tmp.begin()};
        std::set_union(s1.cbegin(), s1.cend(), s2.cbegin(), s2.cend(), ins);
        return tmp;
    };

    bool flag = true;
    while(flag) {
        flag = false;
        for(auto && [x,y] : smap) {

            if(y.isTerminal()) {
                continue;
            }

            auto first_old_size = first[x].size();
            auto nullable_old_value = nullable[x];
            // for each production of x
            for(auto && p : y.getCandidates()) {
                auto pos = 0U;
                while(pos < p.size() && nullable[p[pos]]) {
                    first[x] = myunion(first[x], first[p[pos]]);
                    ++pos;
                }
                
                if(pos < p.size()) {
                    first[x] = myunion(first[x], first[p[pos]]);
                }else {
                    nullable[x] = true;
                }



                auto pos2 = (long)(p.size() - 1);
                while(pos2 >= 0 && nullable[p[pos2]]) {
                    auto old = follow[p[pos2]].size();
                    follow[p[pos2]] = myunion(follow[p[pos2]], follow[x]);
                    if(old != follow[p[pos2]].size()) {
                        flag = true;
                    }
                    --pos2;
                }

                if(pos2 >= 0) {
                    auto old = follow[p[pos2]].size();
                    follow[p[pos2]] = myunion(follow[p[pos2]], follow[x]);
                    if(old != follow[p[pos2]].size()) {
                        flag = true;
                    }
                }
                
                auto all = [&nullable](auto c, auto start, auto end){
                    bool ret = true;
                    for(auto i = start; i < end; ++i) {
                        ret = ret && nullable[c[i]];
                    }
                    return ret;
                };


                for(auto i = 0; p.size() && i < p.size() - 1; ++i) {
                    for(auto j = i + 1; j < p.size(); ++j) {
                        if(all(p, i + 1, j - 1)) {
                            auto old = follow[p[i]].size();
                            follow[p[i]] = myunion(follow[p[i]], first[p[j]]);
                            if(old != follow[p[i]].size()) {
                                flag = true;
                            }
                        }
                    }
                }
            }

            if(first_old_size != first[x].size() || nullable_old_value != nullable[x]) {
                flag = true;
            }

        }
    }
    for(auto && [x,y] : first) {
        y.erase('?');
    }
    for(auto && [x,y] : follow) {
        y.erase('?');
    }
    return std::make_tuple(first, follow, nullable);
}

auto predictTableGen(const std::map<char, Symbol> syms,const std::map<char, std::set<char>> first, const std::map<char, std::set<char>> follow,const std::map<char, bool> nullable) {
    std::map<char, std::map<char, std::string>> ret;
    for(auto && [x,y] : syms) {
        if(y.isTerminal()) {
            continue;
        } else {
            ret[x] = {};
        }

        if(nullable.at(x)) {
            ret[x]['#'] = '?';
        }

        for(auto && s : y.getCandidates()) {
            for(auto && c : first.at(s[0])) {
                ret[x][c] = s;
            }

            if(nullable.at(s[0])) {
                for(auto && c : follow.at(x)) {
                    ret[x][c] = s;
                }
            }
        }
    }

    return ret;
}

void predictiveAnalysis(const std::map<char, std::map<char, std::string>> table, const std::string & in,const char start) {
    std::string sym_stack;
    size_t input_pos = 0;
    sym_stack.push_back('#');
    sym_stack.push_back(start);
    auto input = in;
    input.push_back('#');

    auto pretty_print = [&sym_stack, &input_pos, &input](const std::string & p) {
        std::cout << std::left << std::setw(12) 
        << sym_stack << std::left << std::setw(12)
        << (input.c_str() + input_pos) << std::left << std::setw(12)
        << p << std::endl;

    };

    while(!sym_stack.empty() && input_pos != input.size()) {
        char c = input[input_pos];

        if(c == sym_stack.back()) {
            sym_stack.pop_back();
            input_pos++;
            pretty_print("GETNEXT()");
            continue;
        }

        auto && subtable = table.at(sym_stack.back());
        if(subtable.find(c) == subtable.cend()) {
            // not found
            std::cout << "Error\n";
        } else {
            auto && p = subtable.at(c);
            std::string tmp = std::string{sym_stack.back()} + std::string{"->"} + p;
            sym_stack.pop_back();


            if(p[0] != '?')
            for(auto i = (long)(p.size() - 1); i >= 0; --i) {
                sym_stack.push_back(p[i]);
            }
            pretty_print(tmp);
        }
    }
}

int main(void) {
    std::vector<std::string> productions;
    int n;
    std::cin >> n;
    std::string tmp;
    while(n--) {
        std::cin >> tmp;
        productions.push_back(tmp);
    }

    auto syms = symsGen(productions);
    auto [first, follow, nullable] = firstfollowSetGen(syms);
    auto table = predictTableGen(syms, first, follow, nullable);

#ifdef DEBUG

    for(auto && [x, y] : syms) {
        y.print();
        std::cout << std::endl;
    }

    for(auto && [x, y] : first) {
        std::cout << "Frist set of " << x << ": ";
        for(auto && z : y) {
            std::cout << z << ", ";
        };
        std::cout << std::endl;
    }

    for(auto && [x, y] : follow) {
        std::cout << "follow set of " << x << ": ";
        for(auto && z : y) {
            std::cout << z << ", ";
        };
        std::cout << std::endl;
    }

    for(auto && [x,y] : nullable) {
        std::cout << "Nullable(\'" << x << "\') = " << y << std::endl;
    }


    for(auto && [x1, y1] : table) {
        for(auto && [x2, y2] : y1) {
            std::cout << "T(" << x1 << ", " << x2 << ") = " << y2 << std::endl;
        }
    }
#endif // DEBUG

    predictiveAnalysis(table, "i*i+i", 'E');


    return 0;
}