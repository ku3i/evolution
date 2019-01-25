/*---------------------------------+
 | Matthias Kubisch                |
 | kubisch@informatik.hu-berlin.de |
 | July 2017                       |
 +---------------------------------*/

#include <common/application_base.h>
#include <common/event_manager.h>
#include <common/log_messages.h>
#include <common/basic.h>

#include <robots/simloid.h>
#include <robots/simloid_log.h>
#include <control/jointcontrol.h>
#include <control/controlparameter.h>

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
    Evaluation(const Setting& settings, Datalog& logger, robots::Simloid& robot, control::Jointcontrol& control, control::Control_Parameter& param0, uint64_t& cycles)
    : settings(settings)
    , logger(logger)
    , robot(robot)
    , control(control)
    , param0(param0)
    , fitness_function(assign_fitness(robot, settings))
    , data()
    , verbose(settings.visuals)
    , cycles(cycles)
    , robot_log(robot)
    , axis_position_xy(.5, -.50, .0, 1., 1.0, 0, "xy-position")
    , axis_position_z(-.5, -.25, .0, 1., 0.5, 1,  "z-position", 0.1)
    , plot_position_xy(std::min(10000u, settings.max_steps), axis_position_xy, colors::white)
    , plot_position_z (std::min(10000u, settings.max_steps), axis_position_z , colors::cyan)
    , plot_rotation_z (std::min(10000u, settings.max_steps), axis_position_z , colors::magenta)
    , plot_velocity_y (std::min(10000u, settings.max_steps), axis_position_z , colors::yellow)
    /**TODO print out mutation rate average and std dev */
    {
        sts_msg("Creating evaluation function.");

        /** setting the initial controller is needed
         * to define the symmetry for rest of the trials */
        control.set_control_parameter(param0);

        /* prepare frame recording */
        if (logger.is_video_included())
            robot.record_next_frame();

        robot.set_low_sensor_quality(settings.low_sensor_quality);
    }
    bool evaluate(Fitness_Value &fitness, const std::vector<double>& genome, double rand_value);
    void prepare_generation(unsigned cur_generation, unsigned max_generation);
    void prepare_evaluation(unsigned cur_trial, unsigned max_trial);
    void draw(void) const;
    void logdata(uint32_t, uint32_t);

private:
    const Setting&              settings;
    Datalog&                    logger;
    robots::Simloid&            robot;
    control::Jointcontrol&      control;
    control::Control_Parameter& param0;
    Fitness_ptr                 fitness_function;
    fitness_data                data;
    const bool                  verbose;
    uint64_t&                   cycles;

    double                      rnd_amplitude = .0;

    /*logs*/
    robots::Simloid_Log         robot_log;

    /* drawing */
    axes axis_position_xy;
    axes axis_position_z;

    plot2D plot_position_xy;
    plot1D plot_position_z;
    plot1D plot_rotation_z;
    plot1D plot_velocity_y;
};


std::vector<double> create_motor_params(Setting const& settings) {
    if ("NONE" == settings.rnd.mode) return {};
    else return {static_cast<double>(settings.rnd.init), settings.rnd.value};
}

class Application : public Application_Base
{
    typedef std::unique_ptr<Evolution> Evolution_ptr;

public:
    Application(int argc, char** argv, Event_Manager& em)
    : Application_Base(argc, argv, em, "Evolution", 640, 640)
    , settings(argc, argv)
    , robot(settings.tcp_port, settings.robot_ID, settings.scene_ID, settings.visuals, /*realtime =*/ true, create_motor_params(settings))
    , control(robot)
    , seed( control::initialize_anyhow( robot
                                      , control
                                      , settings.symmetric_controller
                                      , { settings.param_p, settings.param_d, settings.param_m }
                                      , settings.seed ))
    , evaluation(settings, logger, robot, control, seed, cycles)
    , evolution((settings.project_status == NEW) ? new Evolution(evaluation, settings, seed.get_parameter())
                                                 : new Evolution(evaluation, settings, (settings.project_status == WATCH)))
    , axis_fitness(.5, .5, .0, 1., 1.0, 1, "Fitness")
    , plot1D_max_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::white)
    , plot1D_avg_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::orange)
    , plot1D_min_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::pidgin)
    , axis_mutation(-.5, .5, .0, 1., 1.0, 1, "Mutation")
    , plot1D_max_mutation(std::min(evolution->get_number_of_trials(), 1000lu), axis_mutation, colors::white)
    , plot1D_avg_mutation(std::min(evolution->get_number_of_trials(), 1000lu), axis_mutation, colors::orange)
    , plot1D_min_mutation(std::min(evolution->get_number_of_trials(), 1000lu), axis_mutation, colors::pidgin)
    {
        if (not settings.visuals) do_pause.disable(); // no pause with disabled GUI
        sts_msg("Done preparing evolution.");
    }

    ~Application() { dbg_msg("Destroying application."); }

    bool loop();
    void finish();
    void paused(void) { robot.idle(); }
    void draw(const pref&) const;
    bool visuals_enabled(void) { return settings.visuals; }

private:
    Setting                    settings;
    robots::Simloid            robot;
    control::Jointcontrol      control;
    control::Control_Parameter seed;
    Evaluation                 evaluation;
    Evolution_ptr              evolution;

    /* Graphics */
    axes axis_fitness;
    plot1D plot1D_max_fitness;
    plot1D plot1D_avg_fitness;
    plot1D plot1D_min_fitness; /**TODO think about putting all graphics stuff to evolution_graphics class*/

    axes axis_mutation;
    plot1D plot1D_max_mutation;
    plot1D plot1D_avg_mutation;
    plot1D plot1D_min_mutation;
};


