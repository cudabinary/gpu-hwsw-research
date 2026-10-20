CXX ?= g++
CXXFLAGS ?= -std=c++17 -O3 -Wall -Wextra -Werror -pedantic
CPPFLAGS := -Iinclude -Ivendor/consumer/include -Ivendor/consumer/frozen
all: build/scope_probe build/distance_probe
build/scope_probe: src/scope_probe.cpp include/closure_scope.hpp include/stop_bridge.hpp vendor/consumer/src/consumers.cpp
	mkdir -p build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) src/scope_probe.cpp vendor/consumer/src/consumers.cpp -o $@
clean:
	rm -f build/scope_probe
.PHONY: all clean
build/distance_probe: src/distance_probe.cpp include/distance_guard.hpp include/closure_scope.hpp
	mkdir -p build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) src/distance_probe.cpp vendor/consumer/src/consumers.cpp -o $@
