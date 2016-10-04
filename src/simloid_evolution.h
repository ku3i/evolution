#ifndef MAIN_H
#define MAIN_H

#include <cstdio>
#include <cstdlib>
#include <cstdarg>
#include <unistd.h>

#include <ctime>
#include <cmath>
#include <cfloat>
#include <cstring>
#include <cerrno>
#include <clocale>
#include <sys/time.h>
#include <signal.h>
#include <vector>
#include <memory>

#include <common/application_interface.h>
#include <common/event_manager.h>
#include <common/log_messages.h>
#include <common/basic.h>

#include <robots/simloid.h>

#include <evolution/evolution.h>
#include <evolution/setting.h>
#include <evolution/fitness.h>
#include <evolution/generation_based_strategy.h>

#include <basic/color.h>

/* drawing */
#include <draw/draw.h>
#include <draw/axes.h>
#include <draw/plot1D.h>
#include <draw/plot2D.h>

extern GlobalFlag do_pause;

class Evaluation : public virtual Evaluation_Interface
{
public:
    Evaluation(const Setting &settings, robots::Simloid &robot, Jointcontroller &control)
    : settings(settings)
    , robot(robot)
    , control(control)
    , fitness_function(assign_fitness(robot, settings))
    , verbose(settings.visuals)
    , axis_position_xy(.5, -.50, .0, 1., 1.0, 0, "xy-position")
    , axis_position_z(-.5, -.25, .0, 1., 0.5, 1,  "z-position")
    , plot_position_xy(std::min(10000u, settings.max_steps), axis_position_xy, colors::white)
    , plot_position_z(std::min(10000u, settings.max_steps), axis_position_z, colors::white)
    , plot_rotation_z(std::min(10000u, settings.max_steps), axis_position_z, colors::brown)
    {
        sts_msg("Creating evaluation function.");
    }
    bool evaluate(Fitness_Value &fitness, const std::vector<double>& genome, double rand_value);
    void prepare(void);
    void draw(void) const;

private:
    const Setting&   settings;
    robots::Simloid& robot;
    Jointcontroller& control;
    Fitness_ptr      fitness_function;
    const bool       verbose;

    /* drawing */
    axes axis_position_xy;
    axes axis_position_z;

    plot2D plot_position_xy;
    plot1D plot_position_z;
    plot1D plot_rotation_z;
};

/* TODO: integrate a tournament mode:
 * let all individuals (selection) be evaluated a certain number of trials,
 * then average their fitnesses and save the best one as final result into
 * a *.seed file. */

/* TODO: think about how to implement randomized starting positions to make evolved behavior
 * more robust. really, do it! */

class Application : public Application_Interface, public Application_Base
{
    typedef std::unique_ptr<Evolution> Evolution_ptr;

public:
    Application(int argc, char **argv, Event_Manager &em)
    : Application_Base("Evolution", 800, 800)
    , settings(argc, argv)
    , event(em)
    , robot(settings.tcp_port, settings.robot_ID, settings.scene_ID, settings.visuals)
    , control(robot.get_robot_config(),
              settings.symmetric_controller,
              settings.param_p,
              settings.param_d,
              settings.param_m,
              settings.seed)
    , evaluation(settings, robot, control)
    , evolution((settings.project_status == NEW) ? new Evolution(evaluation, settings, control.get_control_parameter())
                                                 : new Evolution(evaluation, settings, (settings.project_status == WATCH)))
    , cycles(0)
    , axis_fitness(.0, .5, .0, 2., 1., 1, "Fitness")
    , plot1D_max_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::white)
    , plot1D_avg_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::orange)
    , plot1D_min_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::pidgin)
    {
        if (not settings.visuals) do_pause.disable(); // no pause with disabled GUI
        sts_msg("Done preparing evolution.");
    }

    ~Application() { dbg_msg("Destroying application."); }

    void setup();
    bool loop();
    void finish();
    void draw(const pref&) const;
    bool visuals_enabled(void) { return settings.visuals; }
    uint64_t get_cycle_count(void) const { return cycles; }

private:
    Setting         settings;
    Event_Manager&  event;
    robots::Simloid robot;
    Jointcontroller control;
    Evaluation      evaluation;
    Evolution_ptr   evolution;
    uint64_t        cycles;

    /* Graphics */
    axes axis_fitness;
    plot1D plot1D_max_fitness;
    plot1D plot1D_avg_fitness;
    plot1D plot1D_min_fitness; //TODO think about putting all graphics stuff to evolution_graphics class
};

#endif /*MAIN_H*/

