#include "TFile.h"
#include "TTree.h"
#include "TG4Event.h"

#include <vector>
#include <cstdio> 


double getProductionTime_PNS(double pulse_width) {

    /*
    This function generates a random time within 
    the duration of the pulse width 

    Args
        double pulse_width: self-explaining 

    Returns
        double t: random time in pulse 
    
    */

    // Set UUID seed 
    gRandom = new TRandom3(0);
    double t;
    t = gRandom->Uniform(pulse_width); 
    return t;
  
  }
  
  struct TaggedTime {
    double time;
    int tag;
    TaggedTime(double time, int tag) :
      time(time), tag(tag) {}
    TaggedTime() : time(0), tag(0) {}
  };


  double DTG_neutron_yield_calculator(double acc_voltage, double ion_current){

    /* 
    This function calculates the neutrion yield (n/s) according
    to the functions estimated in the DTG MC paper. The uncertainty
    on this number is ~25% according to the manufacturer. 

    Args
        acc_voltage: Adjustable acceleration voltage at the tritium target
        ion_current: Adjustable deuterium current 

    Returns
        n_yield: Neutron yield (n/s) for the chosen settings 

    */


    double n_yield = 0.;


    if(ion_current == 60){
        n_yield = -1.48e2*(TMath::Power(acc_voltage,3)) + 7.196e4*(TMath::Power(acc_voltage,2)) - 4.439e6*(acc_voltage) + 8.05e7; 
        
    }

    else if(ion_current == 40){
        n_yield = -9.891e1*(TMath::Power(acc_voltage,3)) + 4.797e4*(TMath::Power(acc_voltage,2)) - 2.960e6*(acc_voltage) + 5.37e7;
    }

    else if(ion_current == 20){
        n_yield = 1.946e2*(TMath::Power(acc_voltage,3)) - 2.099e4*(TMath::Power(acc_voltage,2)) + 1.12e6*acc_voltage - 2.121e7;
    }

    else{
        std::cout << "Ion current value not valid, returning non-physical value" << std::endl;
        return -1.;
    }

    return n_yield;
}


int create_neutron_pulses(std::string input_file, 
                          int spillFileId, 
                          double PULSE_WIDTH, 
                          double ACC_VOLTAGE,
                          double CURRENT,
                          double DUTY_FACTOR,
                          std::string output_file="2x2_DTG_edepsim_rectified_spill.root"){

    /*
                        
    This function reads an edep-sim file containing only primary neutrons
    and creates a new file containing DT-like pulses. 

    Args:
        input_file: path to your input edep-sim file
        spillFileId: index of the input file 
        PULSE_WIDTH: Desired pulse width in s
        ACC_VOLTAGE: Acceleration voltage at tritium target (kV)
        CURRENT: deuterium current value (uA)
        FREQUENCY: Number of pulses per second (hz)
        DUTY_FACTOR: Percentage of time the DT is emitting pulses 
        output_file: name of your output .root file 

      
    TO DO: Need to calculate the pulse period in function using 
    the value of the frequency and the duty factor 
    
    */



    std::cout << "======================================================" << std::endl;
    printf("Creating neutron pulses with the following settings:\n");
    double NEUTRON_YIELD = DTG_neutron_yield_calculator(ACC_VOLTAGE, CURRENT);
    double FREQUENCY = 1.*DUTY_FACTOR/PULSE_WIDTH;
    double TIME_BETWEEN_PULSES = (1 - DUTY_FACTOR)/(FREQUENCY - 1);
    double PULSE_PERIOD = 1.2; // Fixed 1.2s

    printf("Duty factor %.3f \n", DUTY_FACTOR);
    printf("Pulse width: %.1e us\n", PULSE_WIDTH*1e6);
    printf("Time between pulses: %.1f us\n", TIME_BETWEEN_PULSES*1e6);
    printf("Forced time bt pulses %.1f s \n", PULSE_PERIOD);
    printf("Frequency: %1.f hz \n", FREQUENCY);
    printf("Calculated neutron yield: %.1e n/s\n", NEUTRON_YIELD);
    printf("Average number of neutrons per pulse: %.1f \n", std::floor(NEUTRON_YIELD/FREQUENCY));

    double T_PULSES=100; // number of equivalent pulses  
    double N_PULSES=1; // Number of pulses to simulate
    
    TFile *inputFile = TFile::Open(input_file.c_str());
    auto geom = (TGeoManager*) inputFile->Get("EDepSimGeometry");
    TTree* events = (TTree*) inputFile->Get("EDepSimEvents");
    TG4Event* event = NULL;
    events->SetBranchAddress("Event", &event);
    Long64_t nEntries = events->GetEntries();

    printf("Number of neutron events in input file:  %i \n", nEntries);
    if(nEntries < NEUTRON_YIELD/FREQUENCY){
      std::cout << "Not enough neutrons to create at least one pulse..." << std::endl;
      return 1;
    }



    // Determine the events per pulse
    double evts_per_pulse = 0.;
    evts_per_pulse = NEUTRON_YIELD/FREQUENCY;
    printf("Output file name: %s \n", output_file.c_str());
    printf("======================================================\n");

    TFile *outFile = new TFile(output_file.c_str(), "RECREATE");
    TTree *newTree = events->CloneTree(0);  // Create an empty copy of the tree structure

    int evt_out = 0;

    // SET UUID seed 
    gRandom = new TRandom3(0);
    // Iterate over pulses 

    TMap *event_spill_map = new TMap(nEntries);


    int ipulse=1;
    bool debug_pulse=false;
    while(true){

        if(debug_pulse && ipulse == 10){break;}

        // Include 25% uncerainty on neutron yield
        // If nevets_this_pulse 0, try again (?)
        int Nevts_this_pulse = gRandom->Gaus(evts_per_pulse,evts_per_pulse*0.25);

        // Create a vector of size #neutrons in this pulse 
        std::vector<TaggedTime> times(Nevts_this_pulse);

        // Generate times and sort them 
        std::generate(times.begin(),
                      times.begin() + Nevts_this_pulse,
                      [PULSE_WIDTH]() { return TaggedTime(getProductionTime_PNS(PULSE_WIDTH), 1); });
        std::sort(times.begin(),
                  times.end(),
                  [](const auto& lhs, const auto& rhs) { return lhs.time < rhs.time; });


        // We finish if we ran out of neutrons...

        if(evt_out + Nevts_this_pulse >  nEntries){
            break;
        }
        std::cout << "Pulse: " << ipulse << ", Number of neutrons: " << Nevts_this_pulse << std::endl;
        double this_pulse_time = (1e9)*PULSE_PERIOD*(ipulse); // in ns 
        std::cout << "This pulse time: " << this_pulse_time*1e-9 << " s" << std::endl;
        // Iterate over the number of neutrons in this pulse
        for (const auto& ttime : times) {
            events->GetEntry(evt_out);
            int globalSpillId = int(1E3)*spillFileId + ipulse;

            std::string event_string = std::to_string(event->RunId) + " " + std::to_string(event->EventId);
            std::string spill_string = std::to_string(globalSpillId);
            TObjString* event_tobj = new TObjString(event_string.c_str());
            TObjString* spill_tobj = new TObjString(spill_string.c_str());
      
            if (event_spill_map->FindObject(event_string.c_str()) == 0)
              event_spill_map->Add(event_tobj, spill_tobj);
            else {
              std::cerr << "[ERROR] redundant event ID " << event_string.c_str() << std::endl;
              std::cerr << "event_spill_map entries = " << event_spill_map->GetEntries() << std::endl;
              throw;
            }
        
            // We don't start at zero to not crash nd-flow charge2light
            double event_time = ttime.time*1e9 + this_pulse_time; // Align times in ns
            double old_event_time = 0.;
            std::cout << "This neutron (" << evt_out << " " << event->EventId << ") time w.r.t pulse time: " << ttime.time*1e6 << " us"  << std::endl;

            // ... interaction vertex
            for (std::vector<TG4PrimaryVertex>::iterator v = event->Primaries.begin(); v != event->Primaries.end(); ++v) {;
                old_event_time = v->Position.T();
                v->Position.SetT(event_time);
                v->InteractionNumber = evt_out;
            }

            // ... trajectories
            for (std::vector<TG4Trajectory>::iterator t = event->Trajectories.begin(); t != event->Trajectories.end(); ++t) {
                // loop over all points in the trajectory
                for (std::vector<TG4TrajectoryPoint>::iterator p = t->Points.begin(); p != t->Points.end(); ++p) {
                double offset = p->Position.T() - old_event_time;
                p->Position.SetT(event_time + offset);
                }
            }

            // ... and, finally, energy depositions
            for (auto d = event->SegmentDetectors.begin(); d != event->SegmentDetectors.end(); ++d) {
                for (std::vector<TG4HitSegment>::iterator h = d->second.begin(); h != d->second.end(); ++h) {
                double start_offset = h->Start.T() - old_event_time;
                double stop_offset = h->Stop.T() - old_event_time;
                h->Start.SetT(event_time + start_offset);
                h->Stop.SetT(event_time + stop_offset);
                }
            }

            newTree->Fill();
            evt_out++;

        } 
        if(times.size() > 0){
          ipulse++;
        }
        else{
          continue;
        }
    }
    newTree->Write();
    event_spill_map->Write("event_spill_map", 1);
    auto p = new TParameter<double>("spillPeriod_s", PULSE_PERIOD);
    p->Write();
    geom->Write();
    outFile->Close();
    return 0;
}