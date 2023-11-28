package me.shukawam.lemon;

import java.io.IOException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.oracle.bmc.aivision.AIServiceVisionClient;
import com.oracle.bmc.aivision.model.AnalyzeImageDetails;
import com.oracle.bmc.aivision.model.AnalyzeImageResult;
import com.oracle.bmc.aivision.model.ImageClassificationFeature;
import com.oracle.bmc.aivision.model.ImageFeature;
import com.oracle.bmc.aivision.model.InlineImageDetails;
import com.oracle.bmc.aivision.requests.AnalyzeImageRequest;

import io.micronaut.context.annotation.Value;
import io.micronaut.http.multipart.StreamingFileUpload;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

@Singleton
public class LemonQualityService {
    private static final Logger logger = LoggerFactory.getLogger(LemonQualityService.class);
    private final AIServiceVisionClient client;
    private final ResultService resultService;

    private final String compartmentOcid;
    private final String modelOcid;

    @Inject
    public LemonQualityService(AIServiceVisionClient client, ResultService resultService,
            @Value("${oci.compartment-ocid}") String compartmentOcid,
            @Value("${oci.services.vision.model-ocid}") String modelOcid) {
        this.client = client;
        this.resultService = resultService;
        logger.debug("Initialized config properties. compartmentOcid: %s, modelOcid: %s", compartmentOcid, modelOcid);
        this.compartmentOcid = compartmentOcid;
        this.modelOcid = modelOcid;
    }

    public AnalyzeImageResult analyzeImage(StreamingFileUpload file) {
        List<ImageFeature> features = Arrays.asList(ImageClassificationFeature.builder().modelId(modelOcid).build());
        try {
            var response = client.analyzeImage(
                    AnalyzeImageRequest.builder().analyzeImageDetails(
                            AnalyzeImageDetails.builder().compartmentId(compartmentOcid).image(
                                    InlineImageDetails.builder().data(file.asInputStream().readAllBytes()).build())
                                    .features(features)
                                    .build())
                            .build());
            if (response == null) {
                logger.info("Analyze Image Response is null.");
                throw new RuntimeException();
            }
            var analyzeImageResult = response.getAnalyzeImageResult();
            logger.info("analyzeImageResult: %s", analyzeImageResult);
            var parsedLabels = parseLabels(analyzeImageResult);
            // save result to database.
            var isSaved = resultService.saveResult(file.getFilename(), parsedLabels.get("bad_quality"),
                    parsedLabels.get("good_quality"), parsedLabels.get("empty_background"));
            if (!isSaved) {
                throw new RuntimeException("Saving result is failed.");
            } else {
                return analyzeImageResult;
            }
        } catch (IOException e) {
            logger.error("Input file is invalid.", e);
            throw new RuntimeException("Input file is invalid.");
        }
    }

    private Map<String, Float> parseLabels(AnalyzeImageResult analyzeImageResult) {
        var labels = analyzeImageResult.getLabels();
        var parsedLabels = new HashMap<String, Float>();
        labels.forEach(label -> {
            switch (label.getName()) {
                case "bad_quality":
                    parsedLabels.put("bad_quality", label.getConfidence());
                    break;
                case "good_quality":
                    parsedLabels.put("good_quality", label.getConfidence());
                    break;
                case "empty_background":
                    parsedLabels.put("empty_background", label.getConfidence());
                    break;
            }
        });
        return parsedLabels;
    }
}
