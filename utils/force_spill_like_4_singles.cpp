#include "TFile.h"
#include "TTree.h"
#include <vector>
#include "TG4Event.h"
#include "TLorentzVector.h"

void force_spill_like_4_singles(std::string input_file,
                           std::string output_file="spill_like_edep-sim.root",
                           int spillFileId=1){

    /*
    
    ROOT macro that modifies the starting time of each event. Each event
    will be separated by 1.2 s. 


    Args: 
        std::string input_file: Name of the edep-sim input file
        std::string output_file: Name of the filtered edep-sim output file 
        int spillFileId: Index of your file 


    to run:

    root -l -b -q -e "gSystem->Load(\"$LIBTG4EVENT_DIR/libTG4Event.so\")" \
                     "force_spill_like_4_singles.C(\"input_file.root\", \"output_file.root\")"
    
    */

    bool verbose = true; 
    double EVENT_PERIOD = 1.2; // in s 

     
    TFile *inputFile = TFile::Open(input_file.c_str());
    auto geom = (TGeoManager*) inputFile->Get("EDepSimGeometry");
    TTree* events = (TTree*) inputFile->Get("EDepSimEvents");
    TG4Event* event = NULL;
    events->SetBranchAddress("Event", &event);
    Long64_t nEntries = events->GetEntries();
    std::cout << "Number of events in input file: " << nEntries << std::endl;

    // Create a new file to keep capture events:
    TFile *outFile = new TFile(output_file.c_str(), "RECREATE");
    // Create an empty copy of the tree structure
    TTree *newTree = events->CloneTree(0);  
    TMap *event_spill_map = new TMap(nEntries);


    // Iterate over entries and modify time.  
    for(Long64_t i=0; i < nEntries; i++){
        events->GetEntry(i);
        std::vector<TG4Trajectory> trajs= event->Trajectories;
        int nTrajs = trajs.size();

        int globalSpillId = int(1E3)*spillFileId + (i+1);
        double event_time = (1e9)*EVENT_PERIOD*(i+1);
        double old_event_time = 0.;


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

        // Modify times 
        // ... interaction vertex
        for (std::vector<TG4PrimaryVertex>::iterator v = event->Primaries.begin(); v != event->Primaries.end(); ++v) {
            old_event_time = v->Position.T();
            v->Position.SetT(event_time);
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
        newTree->Fill()
    }
    newTree->Write();
    geom->Write();
    event_spill_map->Write("event_spill_map", 1);
    auto p = new TParameter<double>("spillPeriod_s", EVENT_PERIOD);
    p->Write();
    outFile->Close();
}