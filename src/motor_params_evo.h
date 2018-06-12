#ifndef MOTOR_PARAMS_EVO_H_INCLUDED
#define MOTOR_PARAMS_EVO_H_INCLUDED

/*---------------------------------+
 | Matthias Kubisch                |
 | kubisch@informatik.hu-berlin.de |
 | June 2018                       |
 +---------------------------------*/

#include <common/application_base.h>
#include <common/event_manager.h>
#include <common/log_messages.h>
#include <common/file_io.h>
#include <common/basic.h>

#include <robots/simloid.h>
#include <robots/simloid_log.h>

#include <evolution/evolution.h>
#include <evolution/setting.h>
#include <evolution/generation_based_strategy.h>

#include <basic/color.h>
#include <build/params.h>

/* drawing */
#include <draw/draw.h>
#include <draw/axes.h>
#include <draw/plot1D.h>
#include <draw/plot2D.h>

extern GlobalFlag do_pause;

typedef file_io::CSV_File<double> CSVFile_t;

std::vector<double> prepare_motor_model(void) {
    ActuatorParameters motor_params;
    motor_params.V_in = 12.0; /*Volt*/
    return motor_params.get();
}

std::vector<double> constrain_motor_model(std::vector<double> params)
{
    for (auto& p: params)
        if (p < 0.) {
            p = 0.; // assure non-negative values
            wrn_msg("Motor model: Negative values not allowed.");
        }

    ActuatorParameters conf(params, /*assert_range=*/false);
    conf.V_in = 12.0; // input voltage must be constant

    if (conf.coulomb_friction > conf.sticking_friction) {
        wrn_msg("Motor model: Sticking friction must be greater than coulomb friction.");
        conf.coulomb_friction = conf.sticking_friction;
    }

    return conf.get();
}


namespace constants {
    const unsigned rows = /* time, position and voltage*/3;
    const char* filename = "./data/motorparams/input_data_formatted.log";

    std::vector<double> motor_model_seed = prepare_motor_model();
}


class Profile
{
    CSVFile_t input_data;
    std::vector<double> data;
    std::size_t length;

    unsigned profile_ptr = 0;

public:

    Profile(std::size_t length) : input_data(constants::filename, length, constants::rows), data(), length(length)
    {
        input_data.read();
        data.assign(constants::rows, .0);
    }

    void reset() { profile_ptr = 0; }
    void step(void)
    {
        input_data.get_line(profile_ptr++, data);
    }

    std::size_t get_length(void) const { return length; }

    double const& get_voltage (void) const { return data[1]; }
    double const& get_position(void) const { return data[2]; }

};

class Controller
{
    robots::Simloid& robot;
    Profile const& profile;


public:

    Controller(robots::Simloid& robot, Profile const& profile) : robot(robot), profile(profile) {}

    void set_model_parameter(std::vector<double> const& params)
    {
        sts_msg("Updating model parameter.");
        robot.reinit_motor_model(constrain_motor_model(params));
    };

    void execute_cycle()
    {
        auto& j = robot.set_joints()[0];
        j.motor.set( profile.get_voltage() );
    }

};

class FitnessFunction {

    robots::Simloid const& robot;
    Profile const& profile;
    double data;
    unsigned steps = 0;
    double max_steps;

    //const double threshold = .0;

public:
    FitnessFunction(robots::Simloid const& robot, Profile const& profile)
    : robot(robot)
    , profile(profile)
    , data()
    , max_steps(profile.get_length())
    {}

    void start() { data = .0; steps = 0; }

    bool step()
    {
        const double val = robot.get_joints()[0].s_ang - profile.get_position();
        data += val*val;
        ++steps;
        return true;//(data < threshold);
    }

    void finish() {
        assert(max_steps >= steps);
        //data += threshold * (max_steps - steps); // assume constant failure from this point on
        /*anything else to do?*/
    }

    double get_value() const { return 1.0/(1.0+data); }
};

class Evaluation : public virtual Evaluation_Interface
{
public:
    Evaluation(const Setting& settings, Datalog& logger, robots::Simloid& robot)
    : settings(settings)
    , logger(logger)
    , profile(settings.max_steps)
    , robot(robot)
    , control(robot, profile)
    , fitness_function(robot, profile)
    , robot_log(robot)
    , axis_ux(.0, -.50, .0, 3.96, 0.96, 0, "U/X", 0.5)
    , plot_position(std::min(10000u, settings.max_steps), axis_ux, colors::white  )
    , plot_voltage (std::min(10000u, settings.max_steps), axis_ux, colors::magenta)
    , plot_targ_pos(std::min(10000u, settings.max_steps), axis_ux, colors::yellow )
    {
        sts_msg("Creating motor model evaluation function.");

        /* prepare frame recording */
        if (logger.is_video_included())
            robot.record_next_frame();
    }

    bool evaluate(Fitness_Value &fitness, const std::vector<double>& genome, double rand_value);
    void prepare_generation(unsigned cur_generation, unsigned max_generation);
    void draw(void) const;
    void logdata(uint32_t, uint32_t);

private:
    const Setting&         settings;
    Datalog&               logger;
    Profile                profile;

    robots::Simloid&       robot;
    Controller             control;
    FitnessFunction        fitness_function;


    /*logs*/
    robots::Simloid_Log    robot_log;

    /* drawing */
    axes axis_ux;
    plot1D plot_position;
    plot1D plot_voltage;
    plot1D plot_targ_pos;
};


class Application : public Application_Base
{
    typedef std::unique_ptr<Evolution> Evolution_ptr;

public:
    Application(int argc, char** argv, Event_Manager& em)
    : Application_Base(argc, argv, em, "Motor Model Evolution", 800, 400)
    , settings(argc, argv)
    , robot(/*port=*/7890, /*robot=*/81, 0, true)
    , evaluation(settings, logger, robot)
    , evolution((settings.project_status == NEW) ? new Evolution(evaluation, settings, constants::motor_model_seed)
                                                 : new Evolution(evaluation, settings, (settings.project_status == WATCH)))
    , axis_fitness(-1.0, .25, .0, 1.9, 0.5, 1, "Fitness")
    , plot1D_max_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::white)
    , plot1D_avg_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::orange)
    , plot1D_min_fitness(std::min(evolution->get_number_of_trials(), 1000lu), axis_fitness, colors::pidgin)
    , axis_mutation(1.0, .25, .0, 1.9, 0.5, 1, "Mutation")
    , plot1D_max_mutation(std::min(evolution->get_number_of_trials(), 1000lu), axis_mutation, colors::white)
    , plot1D_avg_mutation(std::min(evolution->get_number_of_trials(), 1000lu), axis_mutation, colors::orange)
    , plot1D_min_mutation(std::min(evolution->get_number_of_trials(), 1000lu), axis_mutation, colors::pidgin)
    {
        assert(constants::motor_model_seed.size() == 10);
    }

    bool loop();
    void finish();
    void paused(void) { robot.idle(); }
    void draw(const pref&) const;
    bool visuals_enabled(void) { return settings.visuals; }

private:
    Setting                    settings;
    robots::Simloid            robot;

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


#endif // MOTOR_PARAMS_EVO_H_INCLUDED
