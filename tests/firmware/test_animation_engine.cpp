
#include "AnimationEngine.h"

#include <cassert>
#include <iostream>


void testBlink() {

    AnimationEngine engine;

    engine.reset(
        {4500, false, false},
        0
    );

    assert(!engine.tick(4379).eyesClosed);

    assert(engine.tick(4380).eyesClosed);

    assert(engine.tick(4499).eyesClosed);

    assert(!engine.tick(4500).eyesClosed);

    assert(engine.tick(8880).eyesClosed);
}


void testEarWiggle() {

    AnimationEngine engine;

    engine.reset(
        {0, true, false},
        0
    );

    assert(engine.tick(4199).earOffset == 0);

    assert(engine.tick(4200).earOffset == 4);

    assert(engine.tick(4350).earOffset == -4);

    assert(engine.tick(4500).earOffset == 3);

    assert(engine.tick(4650).earOffset == 0);

    assert(engine.tick(9200).earOffset == 4);
}


void testAccessoryMotion() {

    AnimationEngine engine;

    engine.reset(
        {0, false, true},
        0
    );

    assert(engine.tick(0).accessoryOffset == 0);

    assert(engine.tick(200).accessoryOffset == -2);

    assert(engine.tick(800).accessoryOffset == -8);

    assert(engine.tick(1000).accessoryOffset == -6);

    assert(engine.tick(1600).accessoryOffset == 0);
}


void testDisabled() {

    AnimationEngine engine;

    engine.reset(
        {0, false, false},
        0
    );

    AnimationFrame frame =
        engine.tick(4380);

    assert(!frame.eyesClosed);

    assert(frame.earOffset == 0);

    assert(frame.accessoryOffset == 0);
}


void testReset() {

    AnimationEngine engine;

    engine.reset(
        defaultAnimationSettings(),
        0
    );

    assert(engine.tick(4380).eyesClosed);

    engine.reset(
        defaultAnimationSettings(),
        10000
    );

    AnimationFrame frame =
        engine.tick(10000);

    assert(!frame.eyesClosed);

    assert(frame.earOffset == 0);

    assert(frame.accessoryOffset == 0);
}


void testMillisRollover() {

    AnimationEngine engine;

    engine.reset(
        {1000, false, false},
        UINT32_MAX - 500
    );

    assert(!engine.tick(UINT32_MAX).eyesClosed);

    assert(engine.tick(379).eyesClosed);

    assert(!engine.tick(499).eyesClosed);
}


void testLongGap() {

    AnimationEngine engine;

    engine.reset(
        {4500, true, true},
        0
    );

    AnimationFrame frame =
        engine.tick(4500 * 10 + 4380);

    assert(frame.eyesClosed);

    assert(frame.earOffset == -4);

    assert(frame.accessoryOffset == -4);
}


int main() {

    testBlink();

    testEarWiggle();

    testAccessoryMotion();

    testDisabled();

    testReset();

    testMillisRollover();

    testLongGap();

    std::cout
        << "All 7 animation tests passed\n";
}
